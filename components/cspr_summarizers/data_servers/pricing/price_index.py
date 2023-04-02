"""
Objects responsible for constructing a price index for fungible digital tokens.
The price index could be a time series or a single observation representing the price at a certain block
"""
import sys

from sqlalchemy import text
sys.path.append('../')
import pandas as pd
from data_servers.pricing.pool_implied_price import PoolImpliedPrice

from functools import lru_cache

PRICE_EFFICIENT_POOL_MIN_RESERVE = 200000   # Maximum TVL. Used to determine number of pools we use for pricing
MIN_POOL_SIZE_PER_BLOCK = 0                 # Minimum pool size per block Todo: set back to 100 for production
MAX_PRICE = 10000000                        # Maximum price to not be considered an outlier
MAX_RECURSION = 2                           # 10
MAX_DEPTH = 1

class TokenNotTrackedError(Exception):
    pass


class CouldNotGetPriceError(Exception):
    pass

class PriceIndex:
    def __init__(self, prod_us1_conn, network_read_conn):
        """
        @param prod_us1_conn: read connection to prod_us1
        @param network_read_conn: read connection to the database that contains liquidity pool data. For Ethereum based
        platforms, supply read object to fl_agg_univ2. For BSC, need fl_agg_bsc, etc.
        """
        self.prod_us1_conn = prod_us1_conn
        self.network_read_conn = network_read_conn
        self.pool_implied_price = PoolImpliedPrice(self.network_read_conn)
        self._ntwk_tkn_price = {}
        self._num_recursions = 0

    def _get_timestamp_by_block_number(self, block_number):
        """
        Fetches the timestamp corresponding the given block_number
        :param block_number:
        :return: datetime
        """
        query = f"""
            SELECT timestamp_utc FROM blocks
            WHERE block_number = {block_number}
        """
        return self.network_read_conn.execute(text(query)).fetchone()[0]

    def set_network_read_conn(self, network_read_conn):
        if self.network_read_conn != network_read_conn:
            self.network_read_conn = network_read_conn
            self.pool_implied_price = PoolImpliedPrice(self.network_read_conn)
            self._ntwk_tkn_price = {}
            self._num_recursions = 0

    def set_network_token_price(self, price_per_block, table_name):
        """
        Call this function if you already have the network token prices in memory, so this object doesn't have to
        reload it from the db

        @param price_per_block: A pandas series object containing the price per block
        @param table_name: table name where this price series is stored
        @return:
        """
        self._ntwk_tkn_price[table_name] = price_per_block

    def _get_ntwk_currency_price(self, start_block, end_block, table_name) -> pd.Series:
        """
        Loads and returns network token prices from the database (if needed) and keep them in memory
        @param start_block: starting block, inclusive
        @param end_block: ending block, inclusive
        @return: price per block
        """
        ntwk_token_price_query = """SELECT 
                                block_number, {table_name}_usd
                                FROM {table_name}
                                WHERE block_number BETWEEN {start_block} AND {end_block}
                                ORDER BY block_number"""

        # Case 1: token price is never loaded before
        if table_name not in self._ntwk_tkn_price:
            # Load the price from the db
            query = ntwk_token_price_query.format(start_block=start_block, end_block=end_block, table_name=table_name)
            network_token_price_usd = pd.read_sql(text(query),
                                                  self.network_read_conn,
                                                  index_col='block_number')[f'{table_name}_usd']
            # Store in memory
            self._ntwk_tkn_price[table_name] = network_token_price_usd

        # Case 2: Token price is loaded before, but prices before start_block are needed
        if self._ntwk_tkn_price[table_name].index[0] > start_block:
            _end_block = self._ntwk_tkn_price[table_name].index[0] - 1
            query = ntwk_token_price_query.format(start_block=start_block, end_block=_end_block, table_name=table_name)
            network_token_price_usd = pd.read_sql(text(query),
                                                  self.network_read_conn,
                                                  index_col='block_number')[f'{table_name}_usd']
            # Store it in memory
            self._ntwk_tkn_price[table_name] = network_token_price_usd.append(self._ntwk_tkn_price[table_name])

        # Case 3: Token price is loaded before, but prices before start_block are needed
        if self._ntwk_tkn_price[table_name].index[-1] < end_block:
            _start_block = self._ntwk_tkn_price[table_name].index[-1] + 1
            query = ntwk_token_price_query.format(start_block=_start_block, end_block=end_block, table_name=table_name)
            network_token_price_usd = pd.read_sql(text(query),
                                                  self.network_read_conn,
                                                  index_col='block_number')[f'{table_name}_usd']
            # Store it in memory
            self._ntwk_tkn_price[table_name] = self._ntwk_tkn_price[table_name].append(network_token_price_usd)

        if end_block > self._ntwk_tkn_price[table_name].index[-1]:
            end_block = self._ntwk_tkn_price[table_name].index[-1]
        if start_block < self._ntwk_tkn_price[table_name].index[0]:
            start_block = self._ntwk_tkn_price[table_name].index[0]

        return self._ntwk_tkn_price[table_name].loc[start_block:end_block]

    def _get_pricing_pools(self, address=None, network=None, currency_id=None, block_number=None) -> pd.DataFrame:
        """
        Fetches information about pools needed to price this token.
        Only one of address or currency_id are required
        """
        assert (address and network) or currency_id, "Must provide an address + network or a currency_id"
        # Step 1: Load data from fungible_token_pricing_info
        query = f"""
            SELECT 
                target_token_address,
                target_token_id,
                platform_type,
                pool_name,
                pool_address,
                network,
                pricing_token_address,
                latest_price_timestamp,
                pool_creation_timestamp_utc,
                created_at_block_number,
                target_token_idx,
                lp_watchlevel,
                is_usd_stable_coin,
                is_pricing_token,
                coalesce(latest_poolsize, 0) as latest_poolsize,
                fl_db_name,
                native_currency_table,
                network_token_symbol,
                is_network_currency
            FROM fungible_token_pricing
            WHERE {f"target_token_address='{address}' and network={network}" if address else
                    f"target_token_id={currency_id}"}
        """
        token_pricing_info = pd.read_sql(text(query), self.prod_us1_conn)
        token_pricing_info = token_pricing_info[token_pricing_info['created_at_block_number'] <= block_number]
        if len(token_pricing_info) == 0:
            er = "Token with " + f"address='{address}'" if address else f"currency_id={currency_id}" + f" is not tracked as of block_number= {block_number}"
            raise TokenNotTrackedError(er)
        elif token_pricing_info['is_network_currency'].iloc[0]:
            # Return single record for network tokens
            return token_pricing_info.head(1)

        newly_added_token = pd.isnull(token_pricing_info['latest_price_timestamp'].iloc[0])
        if newly_added_token:
            # This is the first time we price this token. Use up to 5 pools from those available.
            # Use max 5 pools. Order: pool_creation_date, lp_watchlevel, is_network_currency, is_pricing_token
            sort_cols = ['is_pricing_token', 'pool_creation_timestamp_utc', 'lp_watchlevel', 'is_network_currency']
            asc_sort_order = [False, True, False, False]
            token_pricing_info = token_pricing_info.sort_values(by=sort_cols, ascending=asc_sort_order)
            return token_pricing_info.head(6)

        # This is not a newly added token. Use a tracked pool if possible
        if 1 in set(token_pricing_info['lp_watchlevel']):
            token_pricing_info = token_pricing_info[token_pricing_info['lp_watchlevel'] == 1]

        # if there are pricing tokens, drop non-pricing tokens to avoid recursion
        if any(set(token_pricing_info['is_pricing_token'])):
            token_pricing_info = token_pricing_info[token_pricing_info['is_pricing_token']]

        # This is not the first time we price this token, use current large pools
        token_pricing_info = token_pricing_info.sort_values(by='latest_poolsize', ascending=False)
        cumil_poolsize = token_pricing_info['latest_poolsize'].cumsum()
        num_pools = sum(cumil_poolsize < PRICE_EFFICIENT_POOL_MIN_RESERVE) + 1
        return token_pricing_info.head(max(num_pools, 3))

    @lru_cache(4)
    def get_price_index(self, start_block, end_block, address=None, network=1, currency_id=None, depth=0):
        """
        Price index for a fungible token for a given blocks range. Either address or currency id must be provided.
        Use start_block = end_block to get the price at a certain block

        @param depth: for tracking recursion depth
        @param start_block: starting block, inclusive
        @param end_block: closing block, inclusive
        @param address: checksum token address
        @param network: fluidefi network id
        @param currency_id: currency id as per currency table
        @return: price per block, liquidity used per block
        """
        assertion_msg = "Please provide one of: currency_id or address + network"
        assert (address and network) or currency_id is not None, assertion_msg

        #   Step 1: Get the pools needed to construct the price
        pricing_pools = self._get_pricing_pools(address, network, currency_id, start_block)

        #   Step 2: Get an implied price the reserves from each pool
        prices_by_pool = []
        usd_size_by_pool = []
        for _, pricing_pool in pricing_pools.iterrows():
            # Case 2.0: This is a network token
            print("pool_name: ", pricing_pool['pool_name'])
            if pricing_pool['is_network_currency']:
                ntwk_tkn_tbl = pricing_pool['network_token_symbol'] + "_price"
                return self._get_ntwk_currency_price(start_block, end_block, ntwk_tkn_tbl)
            reserves = self.pool_implied_price.get_pricing_info(pricing_pool['platform_type'],
                                                                pricing_pool['pool_address'],
                                                                start_block,
                                                                end_block)
            if len(reserves) == 0:
                continue
            # Pick the latest record per block
            idx = reserves.groupby(['block_number'])['log_index'].transform(max) == reserves['log_index']
            reserves = reserves[idx]
            reserves = reserves.set_index("block_number").sort_index().drop("log_index", axis=1)

            if reserves.index[0] < start_block:
                if len(reserves) == 1 or reserves.index[1] != start_block:
                    reserves.index = [start_block] + list(reserves.index[1:])
                elif reserves.index[1] == start_block:
                    reserves = reserves.loc[start_block:]

            # Case 2.1: We imply the price using the network's token
            if pricing_pool['is_pricing_token'] and not pricing_pool['is_usd_stable_coin']:
                # This is likely a network token. There's a table in the db that has the price per block for this token
                ntwk_tkn_tbl = pricing_pool['network_token_symbol'] + "_price"
                pricing_token_price_usd = self._get_ntwk_currency_price(start_block, end_block, ntwk_tkn_tbl)
            # Case 2.2: We imply the price using a stable coin
            elif pricing_pool['is_pricing_token'] and pricing_pool['is_usd_stable_coin']:
                # this is a stable coin, use it's value
                pricing_token_price_usd = 1
            # Case 2.3: Need to build an optimal path of pools
            else:
                # Need to get the price of this pricing token using other pools.
                if self._num_recursions == MAX_RECURSION or depth == MAX_DEPTH:
                    continue
                self._num_recursions += 1
                pricing_token_price_usd = self.get_price_index(reserves.index[0],
                                                               end_block,
                                                               address=pricing_pool['pricing_token_address'],
                                                               network=pricing_pool['network'],
                                                               depth=depth + 1)

            if pricing_pool['target_token_idx'] == 0:
                reserves.rename({"reserve0": "target_token", "reserve1": "pricing_token"}, axis=1, inplace=True)
            else:
                reserves.rename({"reserve0": "pricing_token", "reserve1": "target_token"}, axis=1, inplace=True)
                reserves["reserve_ratio"] = 1 / reserves["reserve_ratio"]

            # Removing outliers
            reserves = reserves.rolling(min(len(reserves), 3), center=True).median().ffill().bfill()
            reserves['pricing_token_price_usd'] = pricing_token_price_usd
            pool_size = reserves['pricing_token'] * reserves['pricing_token_price_usd'] * 2
            reserves = reserves[pool_size > MIN_POOL_SIZE_PER_BLOCK]
            token_implied_price_usd = reserves["reserve_ratio"] * reserves['pricing_token_price_usd']
            reserves = reserves[token_implied_price_usd < MAX_PRICE]
            if len(reserves) == 0:
                continue
            # extrapolate the reserves
            blocks = range(max(start_block, reserves.index[0]), end_block + 1)
            reserves = reserves.reindex(blocks, method='ffill')
            reserves['pricing_token_price_usd'] = pricing_token_price_usd
            token_implied_price_usd = reserves["reserve_ratio"] * reserves['pricing_token_price_usd']
            pool_size = reserves['pricing_token'] * reserves['pricing_token_price_usd'] * 2
            prices_by_pool.append(token_implied_price_usd)
            usd_size_by_pool.append(pool_size)

        if depth == 0:
            self._num_recursions = 0

        # Step 3: Construct a price index
        sum_weights = pd.concat(usd_size_by_pool, axis=1).fillna(0).sum(axis=1)
        normalized_weights = pd.concat(usd_size_by_pool, axis=1).fillna(0).divide(sum_weights, axis=0)
        price_index = pd.concat(prices_by_pool, axis=1).fillna(0).mul(normalized_weights).sum(axis=1)
        return price_index


if __name__ == '__main__':
    import os
    import sys
    from pathlib import Path
    # import matplotlib.pyplot as plt

    try:
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
    except NameError as e:
        BASE_DIR = Path('exchange_rate.py').resolve().parent.parent.parent
    sys.path.append(os.fspath(BASE_DIR))
    from db_connection_manager import DBConnectionManager

    dbcm = DBConnectionManager()
    prod_us1_conn = dbcm.get_connection("postgres", 'r')
    fl_agg_conn = dbcm.get_connection("postgres", 'r')
    pi = PriceIndex(prod_us1_conn, fl_agg_conn)
    price_index = pi.get_price_index(1393081, 1577646, currency_id=3)
    # price_index = pi._get_ntwk_currency_price(15782284, 15782284, 'native_price')

    print(price_index)
    dbcm.close_all_connections()
