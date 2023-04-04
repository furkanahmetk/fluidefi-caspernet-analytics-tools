import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from sqlalchemy import text
from data_servers.pricing.price_index import PriceIndex

class TokenNotTrackedError(Exception):
    pass


class TokenPricesNotFound(Exception):
    pass

class ExchangeRate:
    """
    Responsible for fetching token prices.
    """
    def __init__(self, prod_us1_conn, fl_agg_conn):
        self.start_date = None
        self.end_date = None
        self.prices = {}                        # {token_id: pd.DataFrame()}
        self.token_address_id_map = {}          # {token_address: token_id}
        self.prod_us1_conn = prod_us1_conn
        self.fl_agg_conn = fl_agg_conn
        self.denomination_currency_id = 1       # =1 default for prices in USD
        self.data_frequency = "H"               # default value is hourly
        self.price_index = PriceIndex(prod_us1_conn, None)

    def set_date_range(self, start_date, end_date):
        # remove timezone information and convert to datetime
        start_date = pd.to_datetime(start_date).replace(tzinfo=None)
        end_date = pd.to_datetime(end_date).replace(tzinfo=None)

        self.start_date = start_date
        self.end_date = end_date
        self.prices = {}

    def set_denomination_currency(self, denomination_currency_id):
        if denomination_currency_id != self.denomination_currency_id:
            self.denomination_currency_id = denomination_currency_id
            self.prices = {}

    def set_data_frequency(self, frequency):
        self.data_frequency = frequency

    def _resample_prices(self, prices_df):
        if self.data_frequency == "H" or len(prices_df) == 0:
            return prices_df
        # Frequency higher than one hour. Aggregate:
        agg_methods = {'open_price': 'first',
                       'close_timestamp_utc': 'last',
                       'open_timestamp_utc': 'first',
                       'close_price': 'last',
                       'high_price': 'max',
                       'low_price': 'min',
                       'all_time_high': 'last',
                       'hours_since_ath': 'last'}
        prices_df = prices_df.copy().set_index("open_timestamp_utc", drop=False)
        prices_df = prices_df.resample(self.data_frequency).agg(agg_methods)
        return prices_df.reset_index(drop=True)

    def _load_token_price(self, token_id):
        """
        Fetches the token's price from the database and stores in the memory (for speed purposes)
        """
        # NOTE: Assumes currency is USD for this version
        query = f"""
            SELECT 
                close as close_price,
                open as open_price,
                high as high_price,
                low as low_price,
                timestamp_utc as open_timestamp_utc,
                timestamp_utc + INTERVAL '1 hour' as close_timestamp_utc,
                ath as all_time_high,
                hrs_since_ath as hours_since_ath
            FROM exchange_rate
            WHERE 
                currency = 1 AND base_currency={token_id} AND
                timestamp_utc BETWEEN '{self.start_date}' AND '{self.end_date}'
        """
        token_prices = pd.read_sql(text(query), self.prod_us1_conn, parse_dates=['open_timestamp_utc', 'close_timestamp_utc'])
        if len(token_prices) > 0:
            token_prices['open_timestamp_utc'] = token_prices['open_timestamp_utc'].dt.tz_convert(None)
            token_prices['close_timestamp_utc'] = token_prices['close_timestamp_utc'].dt.tz_convert(None)
            token_prices = token_prices.fillna(0).replace(to_replace=0, method='ffill')
        return token_prices.dropna(subset=['close_price'])

    def _assert_required_input(self, request_type):
        assert request_type in ['history', 'quote']
        if request_type == 'history':
            assert self.start_date, "Please provide start_date"
            assert self.end_date, "Please provide end_date"
            assert self.data_frequency, "Please provide data_frequency"
        assert self.denomination_currency_id, "Please provide denomination_currency_id"

    def get_token_price_history(self, token_address, network):
        """
        Get the time series of the token's price using the contract address
        """
        if token_address in self.token_address_id_map:
            return self.get_token_price_history_by_id(self.token_address_id_map[token_address])
        query = f"SELECT id FROM currency WHERE token_address='{token_address}' and network_id={network}"
        token_id = self.prod_us1_conn.execute(text(query)).fetchone()
        if token_id is None:
            raise TokenNotTrackedError(f"Unable to find token with address '{token_address}' in the currency table")
        self.token_address_id_map[token_address] = token_id[0]
        return self.get_token_price_history_by_id(self.token_address_id_map[token_address])

    def get_token_price_history_by_id(self, token_id):
        """
        Get the time series of the token's price using the FLUIDEFI currency id
        """
        self._assert_required_input(request_type='history')
        if token_id in self.prices:
            return self._resample_prices(self.prices[token_id])
        self.prices[token_id] = self._load_token_price(token_id)
        if self.prices[token_id].empty:
            raise TokenPricesNotFound(
                f"No prices found for currency_id={token_id} and date range {self.start_date} to {self.end_date}")
        return self._resample_prices(self.prices[token_id])

    def get_cspr_price(self, block_number='latest'):
        query = f"SELECT cspr_price_usd FROM native_price_usd WHERE block_number = {block_number if block_number != 'latest' else '(SELECT MAX(block_number) FROM native_price_usd)'}"
        try:
            return self.fl_agg_conn[1].execute(text(query)).fetchone()[0]
        except Exception as e:
            print("Error getting cspr price: ", e)
            return 0

    def _get_lp_token_price(self, block_number, contract_address, network):
        """
        Gets the lp token price for a UNIv2 clone by block
        """
        # Step 1: get the total supply of the lp token
        lp_token_supply = _get_lp_token_supply(block_number, contract_address, self.fl_agg_conn[network])

        # Step 2: Get the addresses of tokens 0 and token  1
        query = f"SELECT token0_address, token1_address FROM all_pairs WHERE contract_address='{contract_address}'"
        token0_address, token1_address = self.fl_agg_conn[network].execute(query).fetchone()

        # Step 3: get the reserves of the pool
        reserve0, reserve1 = _get_lp_reserves(block_number, contract_address, self.fl_agg_conn[network])
        reserve0 = reserve0 / 10 ** _get_token_decimals_by_address(token0_address, self.fl_agg_conn[network])
        reserve1 = reserve1 / 10 ** _get_token_decimals_by_address(token1_address, self.fl_agg_conn[network])

        # Step 4: get the price of token 0
        self.price_index.set_network_read_conn(self.fl_agg_conn[network])
        price0 = float(self.price_index.get_price_index(block_number, block_number, token0_address, network=network))

        # Step 5: get the price of token 1
        price1 = float(self.price_index.get_price_index(block_number, block_number, token1_address, network=network))

        # Step 6: compute the lp token price
        poolsize_usd = reserve0 * price0 + reserve1 * price1
        lp_token_price = poolsize_usd / lp_token_supply
        return lp_token_price

    def _get_latest_block(self, network):
        """
        Latest block number where all raw events are processed
        :return:
        """
        query = """
            SELECT block_number FROM process_log
            WHERE process_name = 'token_total_supply_consolidator'
        """
        block = self.fl_agg_conn[network].execute(query).fetchone()[0]
        return block - 5

    def get_fungible_token_price_quote(self, block_number, contract_address, is_lp_token, network):
        """
        Get a quote for the ERC20 token at block_number
        :param block_number:
        :param contract_address:
        :param token_type: True if this is a liquidity pool token
        :return:
        """
        max_block_processed = self._get_latest_block(network)
        block_number = min(max_block_processed, block_number)
        self.price_index.set_network_read_conn(self.fl_agg_conn[network])

        if is_lp_token:
            token_price = self._get_lp_token_price(block_number,
                                                   contract_address,
                                                   network=network)
        else:
            token_price = self.price_index.get_price_index(block_number,
                                                           block_number,
                                                           contract_address,
                                                           network=network).iloc[0]

        if self.denomination_currency_id == 1:
            # token price is already in USD
            return token_price

        elif self.denomination_currency_id >= 300:
            # Want a quote in another digital currency. Not fiat
            # Step 1: get the address of the denomination currency
            denom_curr_address = self.prod_us1_conn.execute(text(
                f"SELECT token_address FROM currency WHERE id={self.denomination_currency_id}")).fetchone()[0]
            # if the two addresses are equivalent, no need to compute anything else
            if denom_curr_address == contract_address:
                return 1
            # Step 2: get the price of this denomination currency at the same block
            denom_currency_price = float(self.price_index.get_price_index(block_number, block_number, denom_curr_address))
            # Step 3: get and return the token price:
            return token_price / denom_currency_price
        else:
            # desired quote is in a fiat other than USD. Convert...
            # NOTE: we can't provide exact price using other currencies
            block_date_query = f"SELECT timestamp_utc FROM blocks WHERE block_number = {block_number}"
            block_date = self.fl_agg_conn[network].execute(text(block_date_query)).fetchone()[0].replace(microsecond=0,
                                                                                                   second=0, minute=0)
            token_price_query = f"""SELECT (open + close)/2 * {token_price} price FROM usd_price
                                        WHERE currency={self.denomination_currency_id}
                                        AND timestamp_utc <= '{block_date}' 
                                        ORDER BY timestamp_utc DESC
                                        LIMIT 1"""
            # cost to buy one usd using self.denomination_currency_id.
            token_price = self.prod_us1_conn.execute(token_price_query).fetchone()[0]
            return token_price  # token price in denomination currency


def _get_lp_token_supply(block_number, contract_address, read_conn):
    query = f"""
    SELECT total_supply / 1e18 as total_supply
    FROM token_total_supply
    WHERE block_number <= {block_number} AND token_address = '{contract_address}'
    ORDER BY block_number DESC
    LIMIT 1
    """
    return float(read_conn.execute(query).fetchone()[0])


def _get_lp_reserves(block_number, contract_address, read_conn):
    query = f"""
    SELECT reserve0, reserve1
    FROM raw_pair_sync_event
    WHERE block_number <= {block_number} AND address = '{contract_address}'
    ORDER BY block_number DESC
    LIMIT 1 
    """
    reserve0, reserve1 = read_conn.execute(query).fetchone()
    return float(reserve0), float(reserve1)


def _get_token_decimals_by_address(address, fl_agg_univ2_conn):
    """
    Gets the number of decimals of a given token
    """
    query = f"SELECT decimals FROM tokens WHERE token_address='{address}'"
    results = fl_agg_univ2_conn.execute(query).fetchone()
    if results is not None:
        return results[0]


if __name__ == "__main__":
    # How to use: This is best used through DataServer.
    # This is only to showcase the features offered
    # Import the connection objects
    from db_connection_manager import DBConnectionManager
    import matplotlib.pyplot as plt

    db = DBConnectionManager()
    prod_us1_conn = db.get_connection("postgres", "r")
    fl_agg_univ2_conn = db.get_connection("postgres", "r")

    # Instantiate the object
    exchange_rate_server = ExchangeRate(prod_us1_conn, {1: fl_agg_univ2_conn})

    cols_to_plot = ['open_price', 'close_price', 'high_price', 'low_price', 'all_time_high']
    exchange_rate_server.set_date_range('2023-01-01 08:00:00', '2023-09-20 09:00:00')
    exchange_rate_server.set_denomination_currency(1) 
    exchange_rate_server.set_data_frequency("H")
    cspr_price = exchange_rate_server.get_token_price_history_by_id(6)
    cspr_price.set_index("open_timestamp_utc")[cols_to_plot].plot()
    # print(exchange_rate_server.get_fungible_token_price_quote(14782393, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', False))
    plt.show()

    # close connections
    prod_us1_conn.close()
    fl_agg_univ2_conn.close()

