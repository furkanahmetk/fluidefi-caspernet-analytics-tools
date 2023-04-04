import os
import sys
from pathlib import Path
from sqlalchemy import text
try:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
except NameError as e:
    BASE_DIR = Path('exchange_rate.py').resolve().parent.parent.parent
sys.path.append(os.fspath(BASE_DIR))


try:
    from pricing.price_index import PriceIndex
except:
    from pricing.price_index import PriceIndex

import pandas as pd
from db_connection_manager import DBConnectionManager
from datetime import timedelta, datetime
import concurrent.futures
import numpy as np
from utils import load_blocks_range_df

EXCHANGE_RATE_TBL_NAME = "exchange_rate"
NUM_THREADS = 15

def _load_target_tokens_info(prod_us1_conn, prod_us1_conn_write):
    """

    @param prod_us1_conn:
    @return:
    """
    # load processing start dates for each token
    query = """
        SELECT
           target_token_address,
           target_token_id,
           network,
           fl_db_name,
           network_token_symbol,
           native_currency_table,
           COALESCE (latest_price_timestamp + interval '1 hour', pool_creation_timestamp_utc) AS start_timestamp,
           latest_ath,
           latest_hrs_since_ath,
           refresh_timestamp_utc
        FROM
           fungible_token_pricing
        WHERE 
           target_token_id IS NOT NULL AND lp_watchlevel = 1
    """
    target_tokens = pd.read_sql(text(query), prod_us1_conn, parse_dates=['start_timestamp', 'refresh_timestamp_utc'])
    # latest_dt = prod_us1_conn.execute(f"SELECT MAX(timestamp_utc) + interval '1 hour' "
    #                                   f"FROM {EXCHANGE_RATE_TBL_NAME} "
    #                                   f"WHERE base_currency>1").fetchone()
    # if latest_dt:
    #     latest_dt = latest_dt[0].replace(tzinfo=None)
    #     if target_tokens['refresh_timestamp_utc'].max() < latest_dt < datetime.utcnow():
    #         prod_us1_conn_write.execute("REFRESH MATERIALIZED VIEW fungible_token_pricing;")
    #         return _load_target_tokens_info(prod_us1_conn, prod_us1_conn_write)

    target_tokens = target_tokens.groupby(["target_token_address", "network"]).min().reset_index()
    target_tokens['start_timestamp'] = target_tokens['start_timestamp'].dt.floor("H")
    return target_tokens.sample(frac=1)


def _get_network_token_price(start_block, end_block, table_name, fl_agg_conn):
    """
    Loads network token prices from the database and keep them in memory

    @param start_block:
    @param end_block:
    @param table_name:
    @param fl_agg_conn:
    @return:
    """
    ntwk_token_price_query = f"""SELECT 
                            block_number, {table_name}_usd
                            FROM {table_name}
                            WHERE block_number BETWEEN {start_block} AND {end_block}
                            ORDER BY block_number"""
    network_token_price_usd = pd.read_sql(text(ntwk_token_price_query),
                                          fl_agg_conn,
                                          index_col='block_number')[f'{table_name}_usd']
    return network_token_price_usd


def _get_job_indices(max_num_threads, num_jobs):
    """
    Useful for dividing a set of jobs across multiple threads
    Returns a list of tuples with two elements: index of start and index of end for each set of jobs
    """
    num_threads = min(max_num_threads, num_jobs)
    num_jobs_per_thread = int(round(num_jobs / num_threads+.5, 0))
    job_indices = [(thread_num*num_jobs_per_thread, (thread_num+1)*num_jobs_per_thread)
                   for thread_num in range(num_threads)]
    return job_indices


def _ohlc_from_series(prices) -> tuple:
    """
    Returns the open, high, low and the close price (OHLC) from pd.Series of prices
    @return: tuple
    """
    if len(prices) > 0:
        return prices.iloc[0], prices.max(), prices.min(), prices.iloc[-1]
    return np.nan, np.nan, np.nan, np.nan


def get_ohlc(price_index, blocks_ranges):
    """

    @param price_index:
    @param blocks_ranges:
    @return:
    """
    ohlc_rates = blocks_ranges.apply(
        lambda x: _ohlc_from_series(price_index.loc[x['start_block']:x['end_block']]), axis=1)

    ohlc_rates = ohlc_rates.apply(pd.Series)
    ohlc_rates.columns = ["open", "high", "low", "close"]
    return ohlc_rates


def _append_ath_metrics(ohlc, latest_ath, hrs_since_ath) -> pd.DataFrame:
    """
    Helper function responsible for calculating the all time high and the number of hours since the all time high

    @param ohlc: A dataframe containing open, high, low, and close rates
    @param ath: all time high rate as at the beginning of this dataframe
    @param hrs_since_ath: number of hours as at the beginning of this dataframe
    @return: ohlc with ath metrics
    """
    if pd.isnull(latest_ath):
        # This token was never priced before
        latest_ath = 0
        hrs_since_ath = 0

    ohlc['ath'] = np.maximum(latest_ath, ohlc['high'].expanding().max())
    ohlc['hrs_since_ath'] = ohlc['ath'].groupby((ohlc['ath'] != ohlc['ath'].shift()).cumsum()).cumcount()
    if ohlc['ath'].iloc[0] == latest_ath:
        if 0 in ohlc['hrs_since_ath'].iloc[1:].values:
            # index where there is a new all time high
            idx = ohlc['hrs_since_ath'].iloc[1:][ohlc['hrs_since_ath'].iloc[1:] == 0].idxmax()
            # index right before all time high occurs
            idx = ohlc.loc[:idx].index[-2]
        else:
            idx = None
        ohlc.loc[:idx, 'hrs_since_ath'] += (hrs_since_ath + 1)
    return ohlc


def populate_exchange_rate(tokens, network_token_price, blocks_ranges, dbcm):
    """
    Populates our exchange rate table.

    @param tokens: A dataframe containing pricing information
    @param network_token_price: Series of prices of the network token
    @param blocks_ranges: A dataframe containing the starting and ending block for each hour
    @param dbcm: used to instantiate db connection
    @return: None
    """
    if len(tokens) == 0:
        return

    fl_agg_db_name = tokens.iloc[0]['fl_db_name']
    fl_agg_read = dbcm.get_connection(fl_agg_db_name, "r")
    prod_us1_write = dbcm.get_connection("postgres", "rw")
    prod_us1_read = dbcm.get_connection("postgres", "r")
    pi = PriceIndex(prod_us1_read, fl_agg_read)
    pi.set_network_token_price(network_token_price, tokens.iloc[0]['network_token_symbol'] + "_price")
    for _, token_info in tokens.iterrows():
        try:
            # Used for debugging if token_info['target_token_id'] < 1000:
            target_blocks_ranges = blocks_ranges[token_info['start_timestamp']:]
            start_block, end_block = target_blocks_ranges.iloc[0]['start_block'], target_blocks_ranges.iloc[-1]['end_block']
            price_index = pi.get_price_index(start_block, end_block, currency_id=token_info['target_token_id'])
            if len(price_index) == 0:
                message = f"Skipping {token_info['target_token_address']}, empty price index series."
                print(message)
                continue
            ohlc_rates = get_ohlc(price_index, target_blocks_ranges).dropna()
            ohlc_ath_df = _append_ath_metrics(ohlc_rates, token_info['latest_ath'], token_info['latest_hrs_since_ath'])

            ohlc_ath_df['base_currency'] = token_info['target_token_id']
            ohlc_ath_df['currency'] = 1
            ohlc_ath_df.index.name = "timestamp_utc"
            # print(ohlc_ath_df)

            ohlc_ath_df.to_sql(EXCHANGE_RATE_TBL_NAME,
                               dbcm._fl_agg_cspr_eng_rw,
                               if_exists='append',
                               method='multi',
                               index=True,
                               chunksize=1000)

        except Exception as e:
           print("ERROR:", str(e)[0:500], token_info)
           # print(e, token_info)

    fl_agg_read.close()
    prod_us1_write.close()
    prod_us1_read.close()


def run():
    debug = True
    # Establish connections
    print(f"Establishing connection with max {NUM_THREADS} threads")
    dbcm = DBConnectionManager(NUM_THREADS)
    prod_us1_conn = dbcm.get_connection("postgres", "r")
    prod_us1_conn_write = dbcm.get_connection("postgres", "rw")

    target_tokens = _load_target_tokens_info(prod_us1_conn, prod_us1_conn_write)
    if debug:
        print(target_tokens)
    # target_tokens = target_tokens.sample(frac=.30)
    # target_tokens = target_tokens[target_tokens['target_token_id'].isin([13597])]

    prod_us1_conn_write.close()
    prod_us1_conn.close()

    message = f"Processing {len(target_tokens)} tokens. "
    print(message)

    for network in set(target_tokens['network']):
        # To limit the tokens, create a list of only the tokens
        network_target_tokens = target_tokens[target_tokens['network'] == network]
        fl_agg_db_name = network_target_tokens.iloc[0]['fl_db_name']
        network_token_price_table = network_target_tokens.iloc[0]['network_token_symbol'] + "_price"
        if debug:
            print("network: ", network)
            print("fl_agg_db_name: ", fl_agg_db_name)
            print("network_token_price_table: ", network_token_price_table)
            print("Start time for network: ", network_target_tokens['start_timestamp'].min())

        # Establish connection to this network's db
        fl_agg_conn = dbcm.get_connection(fl_agg_db_name, "r")
        # Set the block range to compute using the last block computed in the tokens table
        blocks_range = load_blocks_range_df(fl_agg_conn, network_target_tokens['start_timestamp'].min())

        # 2023-01-09 09:00:00+00
        # 1501751 = '2023-02-19 16:59:45.024+00' - tested and worked
        # 1580834
        # To have a token recalculate a specific timeframe, specify the datatime below and re-run
        # blocks_range = load_blocks_range_df(fl_agg_conn, '2023-02-19 16:59:45.024+00')
        if debug:
            print(blocks_range)
            print("Starting block: ", blocks_range.iloc[0]['start_block'])
            print("  Ending block: ", blocks_range.iloc[-1]['end_block'])

        network_token_price = _get_network_token_price(start_block=blocks_range.iloc[0]['start_block'],
                                                       end_block=blocks_range.iloc[-1]['end_block'],
                                                       table_name=network_token_price_table,
                                                       fl_agg_conn=fl_agg_conn)
        fl_agg_conn.close()
        # populate_exchange_rate(network_target_tokens, network_token_price, blocks_range, dbcm)
        job_indices = _get_job_indices(NUM_THREADS, len(network_target_tokens))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = [executor.submit(populate_exchange_rate,
                                       network_target_tokens.iloc[start:end],
                                       network_token_price,
                                       blocks_range,
                                       dbcm)
                       for start, end in job_indices]
        for count, result in enumerate(results):
            result.result()

    message = "Closing connections"
    print(message)
    dbcm.close_all_connections()


if __name__ == '__main__':
    run()
