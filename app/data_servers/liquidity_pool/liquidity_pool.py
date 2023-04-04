from abc import ABC, abstractmethod
import pandas as pd


class LiquidityPool(ABC):
    def __init__(self, prod_us1_conn, fl_agg_conn, exchange_rate_server):
        self.prod_us1_conn = prod_us1_conn
        self.fl_agg_conn = fl_agg_conn
        self.exchange_rate_server = exchange_rate_server
        self.common_aggregation_rules = {
            "num_swaps_0": "sum",
            "num_swaps_1": "sum",
            "num_burns": "sum",
            "num_mints": "sum",
            "volume_0": "sum",
            "volume_1": "sum",
            "volume_0_base_curr": "sum",
            "volume_1_base_curr": "sum",
            "volume": "sum",
            "num_liquidity_events": "sum",
            "num_swaps": "sum",
            "transactions_period": "sum",
            "close_reserve_0": "last",
            "close_reserve_1": "last",
            "close_reserve_ratio": "last",
            "close_price_0": "last",
            "all_time_high_0": "max",
            "all_time_high_1": "max",
            "hours_since_ath_1": "last",
            "hours_since_ath_0": "last",
            "close_price_1": "last",
            "close_reserve_0_base_curr": "last",
            "close_reserve_1_base_curr": "last",
            "close_timestamp_utc": "last",
            "close_poolsize": "last",
            "total_croi": "last",
            "investment_growth": 'last',
            "hodl_croi": "last",
            "hodl_token_0_croi": "last",
            "hodl_token_1_croi": "last",
            "impermanent_loss_level": "last",
            "impermanent_loss_impact": "last",
            "token_1_fees_croi": "last",
            "price_change_croi": "last",
            "token_0_fees_croi": "last",
            "fees_croi": "last",
            "open_timestamp_utc": "first",
            "open_reserve_0": "first",
            "open_reserve_1": "first",
            "open_reserve_ratio": "first",
            "open_price_0": "first",
            "open_price_1": "first",
            "open_reserve_0_base_curr": "first",
            "open_reserve_1_base_curr": "first",
            "open_poolsize": "first",
            "high_price_0": "max",
            "high_price_1": "max",
            "low_price_0": "min",
            "low_price_1": "min",
            "total_period_return": lambda x: (x + 1).prod() - 1,
            "price_change_ret": lambda x: (x + 1).prod() - 1,
            "misc_return": lambda x: (x + 1).prod() - 1,
            "token_0_price_return": lambda x: (x + 1).prod() - 1,
            "token_1_price_return": lambda x: (x + 1).prod() - 1,
        }

    @abstractmethod
    def fetch_lp_data(self, start_date, end_date, lp_address, network):
        pass

    @abstractmethod
    def compute_returns(self, lp_summary):
        pass

    @abstractmethod
    def infer_missing_prices(self, lp_summary):
        """

        @param lp_summary:
        @return:
        """

    def _compute_base_currency_metrics(self, lp_summary):
        """
        Creates additional columns to lp_summary that contain base currency denominated pool metrics

        @param lp_summary:
        @return:
        """
        lp_summary['close_reserve_0_base_curr'] = lp_summary['close_price_0'] * lp_summary["close_reserve_0"]
        lp_summary['close_reserve_1_base_curr'] = lp_summary['close_price_1'] * lp_summary["close_reserve_1"]
        # base currency-denominated fields
        lp_summary["volume_0_base_curr"] = lp_summary['close_price_0'] * lp_summary["volume_0"]
        lp_summary["volume_1_base_curr"] = lp_summary['close_price_1'] * lp_summary["volume_1"]
        lp_summary["volume"] = lp_summary["volume_0_base_curr"] + lp_summary["volume_1_base_curr"]
        lp_summary['open_reserve_0_base_curr'] = lp_summary['open_price_0'] * lp_summary["open_reserve_0"]
        lp_summary['open_reserve_1_base_curr'] = lp_summary['open_price_1'] * lp_summary["open_reserve_1"]
        lp_summary["close_poolsize"] = lp_summary['close_reserve_0_base_curr'] + lp_summary[
            'close_reserve_1_base_curr']
        lp_summary["open_poolsize"] = lp_summary['open_reserve_0_base_curr'] + lp_summary[
            'open_reserve_1_base_curr']

    @staticmethod
    def _compute_backward_compatibility_metrics(lp_summary):
        """
        Computes deprecated fields
        @param lp_summary:
        @return:
        """
        # backward compatibility
        lp_summary['num_liquidity_events'] = lp_summary['num_burns'] + lp_summary['num_mints']
        lp_summary['num_swaps'] = lp_summary['num_swaps_0'] + lp_summary['num_swaps_1']
        lp_summary['transactions_period'] = lp_summary['num_liquidity_events'] + lp_summary['num_swaps']
        lp_summary['misc_croi'] = 0
        lp_summary['misc_return'] = 0

    def aggregate_lp_data(self, lp_summary, data_frequency=None):
        """
        Aggregates the hourly liquidity pool data

        """
        for col in self.aggregation_rules:
            if col not in lp_summary:
                lp_summary[col] = None
        if lp_summary.empty:
            return lp_summary
        if data_frequency == "H":
            return lp_summary
        elif data_frequency is not None:
            lp_summary.set_index('open_timestamp_utc', inplace=True, drop=False)
            lp_summary = lp_summary.resample(data_frequency).agg(self.aggregation_rules)
            lp_summary.reset_index(drop=True, inplace=True)

            lp_summary.drop([col for col in lp_summary.columns if "_croi" in col], inplace=True, axis=1)
        return lp_summary

    def get_fungible_token_price(self, token_address, network=1):
        """
        Temporary helper function for fetching prices
        """
        try:
            prices = self.exchange_rate_server.get_token_price_history(token_address, network).set_index("open_timestamp_utc").copy()
            assert not prices.isnull().values.any(), f"WARNING: Missing prices {token_address} on network {network}"
            # TODO: Remove this once prices in DB no longer have 0 values
            prices.replace(to_replace=0, method='ffill', inplace=True)
        except Exception as e:
            prices = pd.DataFrame(columns=['close_price',
                                           'open_price',
                                           'high_price',
                                           'low_price',
                                           'open_timestamp_utc',
                                           'close_timestamp_utc'])
            print(f"EXCEPTION: Couldn't find price for token with address {token_address} on network {network}. Error: {e}")

        return prices.drop("close_timestamp_utc", axis=1)

    def get_lp_summary(self, start_date, end_date, network, lp_address, data_frequency=None):
        """
        @param network:
        @param data_frequency:
        @param lp_address:
        @param end_date:
        @param start_date:
        """
        lp_summary = self.fetch_lp_data(start_date, end_date, lp_address, network)
        # print("IN GET_LP_SUMMARY")
        if lp_summary is None or lp_summary.empty:
            # print("NO SUMMARY DATA!")
            return None
        # print("COMPUTING RETURNS")
        self.compute_returns(lp_summary)
        # print("COMPUTED - NOW AGGREGATING")
        lp_summary = self.aggregate_lp_data(lp_summary, data_frequency)
        return lp_summary

