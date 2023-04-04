"""
Detailed information on liquidity pools.
"""
from sqlalchemy import text
import numpy as np
import pandas as pd
from data_servers.liquidity_pool.univ2_liquidity_pool import UniV2LiquidityPool
# from data_servers.liquidity_pool.univ3_liquidity_pool import UniV3LiquidityPool
# from fluidefi_aggregator.data_servers.liquidity_pool.Univ3_summary_supplementary import jap_lp_summary_v3_copy, lp_summary_v3_py_copy

pd.set_option('use_inf_as_na', True)

# The minimum poolsize required to be added to lp_summary3_latest. $40 is currently the gas fee for removing liquidity.
MIN_POOLSIZE = 40
MAX_POOLSIZE = 10000000000


class UnrecognizedPlatformError(Exception):
    pass


class LPSummary:
    def __init__(self, prod_us1_conn, fl_agg_conn, exchange_rate_server):
        self.prod_us1_conn = prod_us1_conn
        assert isinstance(fl_agg_conn, dict), "Must provide dictionary where key is network id and value is a" \
                                              " connection the the corresponding database"
        self.fl_agg_conn = fl_agg_conn
        self.exchange_rate_server = exchange_rate_server
        self.start_date = None
        self.end_date = None
        self.denomination_currency_id = None
        self.data_frequency = None
        self.univ2_lp = UniV2LiquidityPool(prod_us1_conn, fl_agg_conn, exchange_rate_server)
        # self.univ3_lp = UniV3LiquidityPool(prod_us1_conn, fl_agg_conn, exchange_rate_server)

    def set_fl_agg_conn(self, fl_agg_conn):
        """
        connection to the aggregator db. fl_agg_univ2 for Ethereum, fl_agg_bsc for BSC
        @param fl_agg_conn:
        @return: None
        """
        assert isinstance(fl_agg_conn, dict), "Must provide dictionary where key is network id and value is a" \
                                              " connection the the corresponding database"
        self.fl_agg_conn = fl_agg_conn
        self.univ2_lp.fl_agg_conn = fl_agg_conn
        self.univ3_lp.fl_agg_conn = fl_agg_conn

    def _assert_required_settings(self):
        assert self.start_date is not None, "Please provide start_date"
        assert self.end_date is not None, "Please provide end_date"
        assert self.data_frequency is not None, "Please provide data_frequency"
        assert self.denomination_currency_id is not None, "Please provide denomination_currency_id"

    def set_date_range(self, start_date, end_date):
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=None)
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=None)
        self.exchange_rate_server.set_date_range(start_date, end_date)

    def set_data_frequency(self, frequency):
        self.data_frequency = frequency

    def set_denomination_currency(self, denomination_currency_id):
        self.denomination_currency_id = denomination_currency_id
        self.exchange_rate_server.set_denomination_currency(denomination_currency_id)

    def _get_lp_summary(self, lp_id=None, lp_address=None, network=None, is_snapshot=True):
        """

        @param lp_id:
        @param lp_address:
        @param is_snapshot:
        @return:
        """
        self._assert_required_settings()
        assert lp_id or (lp_address and network), "Must provide one of: lp_id or lp_address and network"

        pool_info_query = f"""
            SELECT 
                platform_id as platform_type, 
                contract_address,
                network_id as network
            FROM liquidity_pool lp
            LEFT JOIN platform ON platform.id = lp.platform_id 
            WHERE {f"lp.contract_address='{lp_address}' AND lp.network_id={network}" if lp_address else f"lp.id={lp_id}"}
        """
        
        platform_type, lp_address, network = self.prod_us1_conn.execute(text(pool_info_query)).fetchone()

        # number of days in period
        num_days = (pd.to_datetime(self.end_date) - pd.to_datetime(self.start_date)).delta / 8.64e+13
        # Todo: replace with non-deprecated function
        # print("Deprecated: ", old_num_days)

        # from datetime import datetime
        # num_days = (pd.to_datetime(self.end_date) - pd.to_datetime(self.start_date))
        # print("Compatible: ", num_days)

        # Uniswap v2 compatible
        lp_summary = self.univ2_lp.get_lp_summary(self.start_date,
                                                    self.end_date,
                                                    lp_address=lp_address,
                                                    network=network,
                                                    data_frequency=None if is_snapshot else self.data_frequency)
        print("lp_summary: ", lp_summary)

        if is_snapshot and lp_summary is not None and not lp_summary.empty:
            lp_summary["total_apy"] = (lp_summary["total_period_return"] + 1) ** (365 / num_days) - 1
            lp_summary["fees_apy"] = (lp_summary["yield_on_lp_fees"] + 1) ** (365 / num_days) - 1

        return lp_summary

    def get_lp_summary_ts(self, lp_id=None, lp_address=None, network=None) -> pd.DataFrame:
        """
        A timeseries summary of a liquidity pool

        @param lp_id: liquidity pool id as per liquidity_pool table
        @param lp_address: checksum liquidity pool address
        """
        data =self._get_lp_summary(lp_id, lp_address, network, False)
        if data is not None:
            data.replace({np.nan: None})
        print("_get_lp_summary: ", data)
        return data

    def get_lp_summary(self, lp_id=None, lp_address=None, network=None) -> pd.DataFrame:
        """
        A snapshot summary of a liquidity pool

        @param lp_id: liquidity pool id as per liquidity_pool table
        @param lp_address: checksum liquidity pool address
        """
        lp_summary = self._get_lp_summary(lp_id, lp_address, network, True)

        # Convert to decimals to percentages
        decimal_indicators = ["_apy", "_apr", "_ret", "yield_", "impermanent_loss_level", "impermanent_loss_impact",
                              "liquidity_change"]
        if lp_summary is None:
            return None
        else:
            for col in lp_summary:
                if any([indicator in col for indicator in decimal_indicators]):
                    lp_summary[col] *= 100
            lp_summary = lp_summary.iloc[0].apply(_round_float)
            lp_summary = self.perform_qa(lp_summary, lp_address)

        return lp_summary.replace({np.nan: None}).to_dict()

    def perform_qa(self, lp_summary, lp_address):
        """
        A QA function. It aims to label a record as outlier or not
        Note: This is only snapshot data. Not for time-series
        """
        notes = []

        if lp_summary["close_poolsize"] < MIN_POOLSIZE:
            notes.append(f"Poolsize too small: {lp_summary['close_poolsize']}")
        if lp_summary["close_poolsize"] > MAX_POOLSIZE:
            notes.append(f"Poolsize too big: {lp_summary['close_poolsize']}")
        if lp_summary['yield_on_lp_fees'] > 9200 or lp_summary['yield_on_lp_fees'] < 0:
            notes.append(f"yield_on_lp_fees is an outlier: {lp_summary['yield_on_lp_fees']}")

        # if lp_summary['yield_on_lp_fees'] > lp_summary['volume'] / lp_summary['close_poolsize'] * 0.3 * max(
        #         1 + lp_summary['token_0_price_return'], 1 + lp_summary['token_1_price_return'], 2):
        #     notes.append(f"yield_on_lp_fees far larger than expected: {lp_summary['yield_on_lp_fees']}")

        if len(notes) > 0:
            lp_summary["notes"] = ", ".join(notes)
            lp_summary["outlier"] = True
            lp_summary["replication_instructions"] = str({
                "start_date": self.start_date,
                "end_date": self.end_date,
                "calculation_currency_id": self.denomination_currency_id,
                "data_frequency": self.data_frequency,
                # "liquidity_pool_id": lp_summary['liquidity_pool_id']
            })
            # ToDo: Disable Temporary - Get data from AWS - Recalc using new price routines
            # print("Recopying jap & lp_summary tables")
            # jap_lp_summary_v3_copy(self.fl_agg_conn[1], lp_address, self.start_date, self.end_date)
            # lp_summary_v3_py_copy(self.fl_agg_conn[1], lp_address, self.start_date, self.end_date)

        else:
            lp_summary["notes"] = ""
            lp_summary["outlier"] = False
            lp_summary["replication_instructions"] = ""
        return lp_summary.replace({np.nan: None})


def _round_float(number, num_dec=3, depth=0):
    """
    A float rounding algorithm for crypto prices.
    >>> shib = 0.0000072316207165
    >>> weth = 3156.261100690869
    >>> round_float(shib)
    0.00000723
    >>> round_float(weth)
    3156.26
    """
    if not isinstance(number, float):
        return number
    elif depth > 30:
        return number
    if abs(number) > 1:
        return round(number / 10 ** depth, num_dec)
    return _round_float(number * 10, num_dec + 1, depth + 1)


if __name__ == "__main__":
    # NOTE: This is best used through DataServer.
    # This is only to showcase the features offered. Please do not use this directly in prod

    # Import the connection objects
    from db_connection_manager import DBConnectionManager
    from exchange_rate import ExchangeRate

    import matplotlib.pyplot as plt
    import time

    start_time = time.time()
    db = DBConnectionManager()
    prod_us1_conn = db.get_connection("postgres", "r")
    fl_agg_conn = {1: db.get_connection("postgres", "r"),
                   2: db.get_connection("postgres", "r")}

    # Example:
    exchange_rate_server = ExchangeRate(prod_us1_conn, None)
    univ2lp = UniV2LiquidityPool(prod_us1_conn, fl_agg_conn, exchange_rate_server)
    lp_summary_server = LPSummary(prod_us1_conn, fl_agg_conn, exchange_rate_server)
    lp_summary_server.set_data_frequency("D")
    lp_summary_server.set_denomination_currency(1)  # USD Dollar
    lp_summary_server.set_date_range('2022-02-08 01:42:27.314 ', '2024-03-08 02:45:27.314 ')
    pools = (1,) #, 14763, 14755)
    ret_df = []
    apy = []
    for pool in pools:
        ts = lp_summary_server.get_lp_summary_ts(lp_id=pool).set_index("close_timestamp_utc")['all_time_high_1']
        ts.name = pool
        ret_df.append(ts)
        lp_summary_server.get_lp_summary(lp_id=pool)
    ret_df = pd.concat(ret_df, axis=1)
    # ts.to_clipboard()
    #
    # ts.to_clipboard()
    print(ts)


    # plt.show()
    # print(lp_summary_server.get_lp_summary(6))
    print("--- %s seconds ---" % (time.time() - start_time))

    # ts_v1 = lp_summary_server.get_v1_lp_summary_ts_by_id(63) # legacy time series
    # print(ts_v1.head())
    # lp_summary_server.set_data_frequency("H")
    # snapshot = lp_summary_server.get_lp_summary(1270)
    # # print("Sample timeseries: \n", ts.head())
    # # print("Legacy timeseries: \n", ts_v1.head())
    # print("Snapshot: \n", snapshot)

    # close connections
    prod_us1_conn.close()
