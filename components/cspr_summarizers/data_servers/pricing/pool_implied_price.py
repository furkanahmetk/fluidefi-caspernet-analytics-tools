import sys
sys.path.append('../')

import pandas as pd
import numpy as np
from sqlalchemy import text


class UnsupportedPlatform(Exception):
    pass


class PoolImpliedPrice:
    def __init__(self, read_conn):
        self.read_conn = read_conn  # a read connection for desired network
        self.uniswap_v2_pool = UniV2Pool(self.read_conn)

    def get_pricing_info(self, platform_type, pool_address, start_block, end_block):
        """
        Reserves and reserve ratio which are needed for our price index

        @param platform_type:
        @param pool_address:
        @param start_block:
        @param end_block:
        @return:
        """

        reserves = self.uniswap_v2_pool.get_reserves_by_block_range(pool_address,
                                                                        start_block,
                                                                        end_block)

        reserves['reserve_ratio'] = reserves['reserve1'] / reserves['reserve0']

        # Remove 0 reserves
        reserves = reserves[(reserves['reserve0'] > 0) & (reserves['reserve1'] > 0)]

        return reserves


def _get_pool_info(pool_address, pool_platform, fl_agg_conn) -> dict:
    """
    given a pool and a platform id, this helper function returns a dict with this data:
    pool_creation_block
    token0_decimals
    token1_decimals

    @param pool_address:
    @param pool_platform:
    @return:
    """
    if pool_platform == 5:
        pool_info_table_name = 'all_pairs'
        pool_creation_col_nam = 'first_mint_event_block_number'

    else:
        raise Exception('Platform not recognized')

    query = f"""
        SELECT 
            {pool_creation_col_nam} AS pool_creation_block,
            token0_decimals as token0_decimal,
            token1_decimals as token1_decimal
        FROM {pool_info_table_name}
        LEFT JOIN erc20_token t0 ON t0.token_address = {pool_info_table_name}.token0_address
        LEFT JOIN erc20_token t1 ON t1.token_address = {pool_info_table_name}.token1_address
        WHERE contract_address='{pool_address}'
    """
    return dict(fl_agg_conn.execute(text(query)).fetchone())


def _read_sql_in_chunks(query, read_conn, chunk_size=250000):
    df = []
    for chunk in pd.read_sql(query, read_conn, chunksize=chunk_size):
        df.append(chunk)
    df = pd.concat(df)
    return df
    # return pd.read_sql(query, read_conn)


class UniV2Pool:
    def __init__(self, read_conn):
        self.read_conn = read_conn

    def get_reserves_by_block_range(self, pool_address, start_block, end_block) -> pd.DataFrame:
        """

        @param pool_address: pool address
        @param start_block: beginning block for the period of interest
        @param end_block: ending block for the period of interest
        @return:
        """
        # TODO: check if there is func to get the record prior to start block
        pool_info = _get_pool_info(pool_address, 5, self.read_conn)
        if start_block > pool_info['pool_creation_block']:
            query = f"""
            WITH pool_reserves AS (
                (SELECT block_number, log_index, reserve0, reserve1
                FROM raw_pair_sync_event
                WHERE address='{pool_address}'
                AND block_number < {start_block}
                ORDER BY block_number DESC, log_index DESC
                LIMIT 1)
                UNION ALL
                (SELECT block_number, log_index, reserve0, reserve1
                FROM raw_pair_sync_event
                WHERE address='{pool_address}' AND
                block_number BETWEEN {start_block} AND {end_block})
            )
            SELECT 
                block_number,
                log_index,
                reserve0 / power(10, {pool_info['token0_decimal']}) as reserve0,
                reserve1 / power(10, {pool_info['token1_decimal']}) as reserve1
            FROM pool_reserves"""
        else:
            query = f"""
            SELECT 
                block_number,
                log_index,
                reserve0 / power(10, {pool_info['token0_decimal']}) as reserve0,
                reserve1 / power(10, {pool_info['token1_decimal']}) as reserve1
            FROM raw_pair_sync_event
            WHERE address='{pool_address}' AND block_number BETWEEN {start_block} AND {end_block}"""
        reserves = _read_sql_in_chunks(text(query), self.read_conn)
        # TODO: remove flash loan tx
        # is_flash_loan = np.where(
        #     ((reserves["amount0_out"] > 0) & (reserves["amount0_in"] > 0)) |
        #     ((reserves["amount1_out"] > 0) & (reserves["amount1_in"] > 0)),
        #     True, False)
        # reserves = reserves[~is_flash_loan]
        return reserves


if __name__ == '__main__':
    from db_connection_manager import DBConnectionManager
    engine = DBConnectionManager()
    conn = engine.get_connection("postgres")
    v2_pool = UniV2Pool(conn)
    poolImpliedPrice = PoolImpliedPrice(conn)
    pip = poolImpliedPrice.get_pricing_info(5, 'cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0', 1393081, 1500000)
    busd = v2_pool.get_reserves_by_block_range('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0', 1393081, 1500000)
    busd.to_csv("busd_v1.csv")
