from sqlalchemy import text
from data_servers.liquidity_pool.liquidity_pool import LiquidityPool
import pandas as pd
from datetime import timedelta
import numpy as np


class UniV2LiquidityPool(LiquidityPool):

    def __init__(self, prod_us1_conn, fl_agg_conn, exchange_rate_server):

        super().__init__(prod_us1_conn, fl_agg_conn, exchange_rate_server)
        self.compound_returns = True
        univ2_rules = {
                "open_lp_token_price": "first",
                "open_lp_token_supply": "first",
                "misc_croi": "last",
                "accumulated_token_1_fees": "last",
                "accumulated_token_0_fees": "last",
                "close_lp_token_price": "last",
                "close_lp_token_supply": "last",
                "hodl_return": lambda x: (x + 1).prod() - 1,
                "yield_on_lp_fees": lambda x: (x + 1).prod() - 1,
                "token_1_fees_return": lambda x: (x + 1).prod() - 1,
                'token_0_fees_return': lambda x: (x + 1).prod() - 1,
            }
        self.aggregation_rules = {**self.common_aggregation_rules, **univ2_rules}


    def fetch_lp_data(self, start_date, end_date, lp_address, network):
        """

        @param lp_id:
        @param lp_address:
        @return:
        """
        lp3_query = f"""SELECT 
                        close_lp_token_supply,
                        num_swaps_0,
                        num_swaps_1,
                        num_burns,
                        num_mints,
                        volume_0,
                        volume_1,
                        open_timestamp_utc,
                        close_reserves_0 as close_reserve_0,
                        close_reserves_1 as close_reserve_1
                    FROM hourly_data
                    WHERE address='{lp_address}'"""
        lp3_query = f"""
            (
                -- Get the latest reserves prior to the period of interest
                {lp3_query}
                AND open_timestamp_utc < '{start_date}' ORDER BY open_timestamp_utc DESC LIMIT 1
            )
            UNION ALL
            (
                {lp3_query}
                AND open_timestamp_utc >= '{start_date}'
                AND close_timestamp_utc <= '{end_date}'
                ORDER BY open_timestamp_utc ASC
            )
        """

        # Step 1: get the data from lp_summary3 table
        # print(lp3_query)
        lp_summary = pd.read_sql(text(lp3_query), self.fl_agg_conn[network], parse_dates=['open_timestamp_utc'])
        if lp_summary.empty:
            print(f"No data in block_summary table for {lp_address} between {start_date} and {end_date}.")
            # empty dataframe
            return lp_summary

        elif lp_summary.isnull().values.any():
            # assert not lp_summary.isnull().values.any(), f"WARNING: Null values in jap_lp_summary_v3 and/or v3_summary_py {lp_address} on network {network} | {start_date} to {end_date}"
            # Use for debugging:
            print(f"WARNING: Null values in block_summary {lp_address} on network {network} | {start_date} to {end_date}")
            print("Total NULLs found: ", lp_summary.isnull().sum())
            return lp_summary

        elif len(lp_summary.index[lp_summary.index.duplicated()]) > 0:
            # assert len(lp_summary.index[lp_summary.index.duplicated()]) == 0, f"WARNING: Found duplicated records in jap_lp_summary_v3 and/or v3_summary_py. {lp_address} on network {network} | {start_date} to {end_date}"
            print(f"WARNING: Found duplicated records in block_summary {lp_address} on network {network} | {start_date} to {end_date}")

        lp_summary['open_timestamp_utc'] = lp_summary['open_timestamp_utc'].dt.tz_convert(None)
        lp_summary.set_index("open_timestamp_utc", inplace=True)
        lp_summary['close_lp_token_supply'] = lp_summary['close_lp_token_supply'].ffill().bfill()

        # initial reserves/token supply for the period are the close value from the record right before
        # the beginning of this period
        close_metrics = ['close_reserve_0', 'close_reserve_1', 'close_lp_token_supply']
        open_metrics = ['open_reserve_0', 'open_reserve_1', 'open_lp_token_supply']
        init_reserve0, init_reserve1, init_lp_token_supply = lp_summary.iloc[0][close_metrics]
        active_pool_hours = list(lp_summary.index)[1:]

        # Fill missing hours
        zero_cols = ["num_swaps_0", "num_swaps_1", "num_burns", "num_mints", "volume_0", "volume_1"]
        dt_range = pd.date_range(max(start_date, lp_summary.index[0]), end_date - timedelta(hours=1), freq="H")

        dups = lp_summary.index[lp_summary.index.duplicated()]
        if len(dups) > 0:
            print(f"WARNING: Found duplicated records in hourly_data table. Address: {lp_address}, time: {dups}")
            print("Dropping duplicates...")
            lp_summary = lp_summary[~lp_summary.index.duplicated(keep='last')]

        lp_summary = lp_summary.reindex(dt_range, method='ffill')
        lp_summary.index.name = "open_timestamp_utc"

        lp_summary.loc[~lp_summary.index.isin(active_pool_hours), zero_cols] = 0
        if lp_summary.empty:
            return lp_summary

        lp_summary[open_metrics] = lp_summary[close_metrics].shift()
        lp_summary.loc[lp_summary.index[0], open_metrics] = init_reserve0, init_reserve1, init_lp_token_supply
        # Get the underlying tokens' prices
        token_address_query = f"""
            SELECT
                token0_address,
                token1_address
            FROM all_pairs
            WHERE contract_address='{lp_address}'"""
        t0_address, t1_address = self.fl_agg_conn[network].execute(text(token_address_query)).fetchone()
        prices_0 = self.get_fungible_token_price(t0_address, network)
        prices_1 = self.get_fungible_token_price(t1_address, network)
        if len(prices_0) == 0 and len(prices_1) == 0:
            print("No prices were found for the underlying tokens of this pool")
            return pd.DataFrame()
        prices_0.columns = [col + "_0" for col in prices_0.columns]
        prices_1.columns = [col + "_1" for col in prices_1.columns]
        lp_summary = lp_summary.join(prices_0, how='inner')
        lp_summary = lp_summary.join(prices_1, how='inner')
        # fill missing prices.
        if len(prices_1) != len(prices_0):
            self.infer_missing_prices(lp_summary)
        lp_summary["close_timestamp_utc"] = lp_summary.index + pd.Timedelta(hours=1)
        lp_summary = lp_summary.reset_index()

        self._compute_base_currency_metrics(lp_summary)
        self._compute_backward_compatibility_metrics(lp_summary)
        lp_summary['open_reserve_ratio'] = lp_summary['open_reserve_0'] / lp_summary['open_reserve_1']
        lp_summary['close_reserve_ratio'] = lp_summary['close_reserve_0'] / lp_summary['close_reserve_1']
        return lp_summary

    def aggregate_lp_data(self, lp_summary, data_frequency=None):
        """
        Aggregates the hourly liquidity pool data

        """
        lp_summary = super().aggregate_lp_data(lp_summary, data_frequency)
        self._compute_base_currency_metrics(lp_summary)
        return lp_summary

    def _compute_base_currency_metrics(self, lp_summary):
        """
        Creates additional columns to lp_summary that contain base currency denominated pool metrics

        @param lp_summary:
        @return:
        """
        super()._compute_base_currency_metrics(lp_summary)
        lp_summary['close_lp_token_price'] = lp_summary["close_poolsize"] / lp_summary['close_lp_token_supply']
        lp_summary['open_lp_token_price'] = lp_summary["open_poolsize"] / lp_summary['open_lp_token_supply']

    @staticmethod
    def compute_impermanent_loss_level(current_reserve_ratio, initial_reserve_ratio):
        price_ratio = initial_reserve_ratio / current_reserve_ratio
        return 2 * (price_ratio ** 0.5) / (1 + price_ratio) - 1

    def infer_missing_prices(self, lp_summary):
        """
        Attempts to fill up the missing prices by assuming equal token reserve values and/or constant prices
        """
        for t in ['open', 'close']:
            # Step 1: use the reserves to determine the missing open and close
            for i in [0, 1]:
                j = 0 if i == 1 else 1
                pi_and_no_pj = (lp_summary[f"{t}_price_{j}"].isnull() & ~lp_summary[f"{t}_price_{i}"].isnull())
                lp_summary.loc[pi_and_no_pj, f"{t}_price_{j}"] = lp_summary[f"{t}_reserve_{i}"] * lp_summary[
                    f"{t}_price_{i}"] / lp_summary[f"{t}_reserve_{j}"]

            # Step 2: fill close prices by carrying forward and backward available prices
            for i in [0, 1]:
                j = 0 if i == 1 else 1
                lp_summary[f"{t}_price_{i}"] = lp_summary[f"{t}_price_{i}"].fillna(method="ffill").fillna(
                    method="bfill")

    def compute_returns(self, lp_summary, init_lp_tokens_invested=None):
        # ToDo: Reserves may be 0 for testnet
        # ToDo: I suggest changing the date entered by the user to a date where the initial reserves are not 0
        # ToDo:  This way, you don't have to handle the errors with 0 -> I highly don't recommend this
        # ToDo:  it'll blow up in many other places, and at the best case, it'll produce ridiculously wrong data
        t1_init_reserve = lp_summary.iloc[0]["open_reserve_1"]
        t0_init_reserve = lp_summary.iloc[0]["open_reserve_0"]
        t1_init_price = lp_summary.iloc[0]["open_price_1"]
        t0_init_price = lp_summary.iloc[0]["open_price_0"]
        lp_token_init_price = lp_summary.iloc[0]["open_lp_token_price"]
        initial_ratio = t1_init_reserve / t0_init_reserve
        current_rr = lp_summary["close_reserve_1"] / lp_summary["close_reserve_0"]
        if init_lp_tokens_invested is None:
            init_lp_tokens_invested = lp_summary.iloc[0]['open_lp_token_supply']  # randomly picked
        # Todo: exact init reserve for lp investor
        pool_share = init_lp_tokens_invested / lp_summary['close_lp_token_supply']
        init_investment = pool_share.iloc[0] * lp_summary['open_poolsize'].iloc[0]
        init_k = t1_init_reserve * t0_init_reserve * (
                init_lp_tokens_invested / lp_summary['open_lp_token_supply'].iloc[0]) ** 2
        # Total return
        lp_summary["total_croi"] = lp_summary['close_lp_token_price'] / lp_token_init_price - 1
        lp_summary["total_period_return"] = (lp_summary["total_croi"] + 1).pct_change()
        lp_summary['investment_growth'] = lp_summary["total_croi"] + 1

        # Token 0 and 1 hodler returns
        hodl_croi = (lp_summary["close_price_1"] / t1_init_price + lp_summary["close_price_0"] / t0_init_price) / 2 - 1
        lp_summary['hodl_croi'] = hodl_croi
        lp_summary['hodl_return'] = (lp_summary['hodl_croi'] + 1).pct_change()

        #  Token 0 only hodler returns
        lp_summary['hodl_token_0_croi'] = lp_summary["close_price_0"] / t0_init_price - 1
        lp_summary['token_0_price_return'] = lp_summary["close_price_0"].pct_change()

        #  Token 1 only hodler returns
        lp_summary['token_1_price_return'] = lp_summary["close_price_1"].pct_change()
        lp_summary['hodl_token_1_croi'] = lp_summary["close_price_1"] / t1_init_price - 1

        # compute impermanent loss relative to the beginning of the period
        lp_summary["impermanent_loss_level"] = current_rr.apply(
            lambda x: self.compute_impermanent_loss_level(x, initial_ratio))
        lp_summary["impermanent_loss_impact"] = lp_summary["impermanent_loss_level"] * (1 + hodl_croi)

        # Return contribution to LP holder form the price change
        lp_summary["price_change_croi"] = lp_summary["impermanent_loss_impact"] + hodl_croi
        lp_summary["price_change_ret"] = (lp_summary["price_change_croi"] + 1).pct_change()

        # Return contribution to LP holder from fees earned

        curr_reserve0_assuming_no_fees = (init_k / current_rr) ** .5

        lp_summary["accumulated_token_1_fees"] = pool_share * lp_summary[
            'close_reserve_1'] - init_k / curr_reserve0_assuming_no_fees
        lp_summary["token_1_fees_croi"] = lp_summary["accumulated_token_1_fees"] * lp_summary[
            "close_price_1"] / init_investment
        lp_summary["token_1_fees_return"] = (lp_summary["token_1_fees_croi"] + 1).pct_change()

        lp_summary["accumulated_token_0_fees"] = pool_share * lp_summary[
            'close_reserve_0'] - curr_reserve0_assuming_no_fees
        lp_summary["token_0_fees_croi"] = lp_summary["accumulated_token_0_fees"] * lp_summary[
            "close_price_0"] / init_investment
        lp_summary["token_0_fees_return"] = (lp_summary["token_0_fees_croi"] + 1).pct_change()

        lp_summary["fees_croi"] = lp_summary["token_1_fees_croi"] + lp_summary["token_0_fees_croi"]
        lp_summary["yield_on_lp_fees"] = (lp_summary["fees_croi"] + 1).pct_change()

        # pct_change results in an empty first observation. Fill it up:
        ret_croi_metrics_map = {
            'total_period_return': 'total_croi',
            'price_change_ret': 'price_change_croi',
            'token_1_price_return': 'hodl_token_1_croi',
            'token_0_price_return': 'hodl_token_0_croi',
            'hodl_return': 'hodl_croi',
            'yield_on_lp_fees': 'fees_croi',
            'token_1_fees_return': 'token_1_fees_croi',
            'token_0_fees_return': 'token_0_fees_croi'
        }

        for ret_metric, croi_metric in ret_croi_metrics_map.items():
            lp_summary.loc[lp_summary.index[0], ret_metric] = lp_summary[croi_metric].iloc[0]
