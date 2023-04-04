import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from data_servers.exchange_rate import ExchangeRate
from data_servers.lp_summary import LPSummary
from data_servers.misc.currency import CurrencyAnalytics
class DataServer:
    """
    Serves data from our database in a format that would be very difficult/inefficient with SQL queries
    Data served include:
    - Liquidity Pool analytics
    - Exchange rates
    """
    def __init__(self, prod_us1_conn, fl_agg_conn):
        self.prod_us1_conn = prod_us1_conn
        self.fl_agg_conn = fl_agg_conn
        assert isinstance(fl_agg_conn, dict), "Must provide dictionary where key is network id and value is a" \
                                              " connection the the corresponding database"
        self.exchange_rate = ExchangeRate(prod_us1_conn, fl_agg_conn)
        self.lp_summary = LPSummary(prod_us1_conn, fl_agg_conn, ExchangeRate(prod_us1_conn, fl_agg_conn))
        self.currency = CurrencyAnalytics(prod_us1_conn, fl_agg_conn, self.exchange_rate)
        self._denomination_currency = None
        self._start_date = None
        self._end_date = None
        self._data_frequency = None

    def set_date_range(self, start_date: str, end_date: str):
        """
        Set the date range for the data you would

        :param start_date: str, start date. Can be any format
        :param end_date: str, start date. Can be any format
        :return: None
        """
        # remove timezone information and convert to datetime
        start_date = pd.to_datetime(start_date).replace(tzinfo=None).floor("H")
        end_date = pd.to_datetime(end_date).replace(tzinfo=None).ceil("H")
        end_date = min(end_date, datetime.utcnow().replace(minute=0, second=0, microsecond=0))

        # update date range
        self.exchange_rate.set_date_range(start_date, end_date)
        self.lp_summary.set_date_range(start_date, end_date)
        self.currency.set_date_range(start_date, end_date)
        self._start_date = start_date
        self._end_date = end_date

    def set_denomination_currency(self, denomination_currency:int):
        """
        Set the currency you would the data to be denominated in

        :param denomination_currency: id of the currency form the currency table
        :return: None
        """
        # Check to see if the denomination_currency exists
        currency_exists = self.prod_us1_conn.execute(text(f"SELECT count(*) FROM currency WHERE id={denomination_currency}")).fetchone()[0]
        assert currency_exists, f"Unrecognized denomination_currency {denomination_currency}"
        self.exchange_rate.set_denomination_currency(denomination_currency)
        self.lp_summary.set_denomination_currency(denomination_currency)
        self._denomination_currency = denomination_currency

    def set_data_frequency(self, frequency):
        """
        Relevant for timeseries data only
        :param frequency: H for Hourly, D for daily, W for Weekly, M for Monthly, Q for quarterly
        :return:
        """
        # Check to see if the data frequency is supported
        assert frequency in ["H", "D", "W", "M", "Q"] or isinstance(frequency, timedelta), "Unrecognized data frequency"
        self.exchange_rate.set_data_frequency(frequency)
        self.lp_summary.set_data_frequency(frequency)
        self._data_frequency = frequency

    def close_connections(self):
        """
        Closes connections provided to this data server
        @return:
        """
        self.prod_us1_conn.close()
        for network in self.fl_agg_conn:
            self.fl_agg_conn[network].close()

    def copy(self):
        """
        Makes a copy of DataServer. No new connections are established
        :return: DataServer
        """
        data_server = DataServer(self.prod_us1_conn, self.fl_agg_conn)
        data_server.set_data_frequency(self._data_frequency)
        data_server.set_date_range(self._start_date, self._end_date)
        data_server.set_denomination_currency(self._denomination_currency)
        return data_server


if __name__ == "__main__":
    # How to use:
    # Import the connection objects
    from db_connection_manager import DBConnectionManager

    db = DBConnectionManager()
    prod_us1_conn = db.get_connection("postgres", "r")
    fl_agg_conn = {1: db.get_connection("postgres", "r"),
                   2: db.get_connection("postgres", "rw")}

    # Instantiate the object
    data_server = DataServer(prod_us1_conn, fl_agg_conn)

    # set the parameters
    data_server.set_data_frequency(timedelta(hours=1))
    data_server.set_denomination_currency(1)                # US Dollar

    # First block on testnet 1501751 = '2023-02-19 16:59:45.024+00'
    data_server.set_date_range('2023-02-19 16:59:45.024+00', '2023-03-27 18:00:00+00')
    address = 'cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0'

    print("------------ get_lp_summary_ts -----------------------")
    lp_summary = data_server.lp_summary.get_lp_summary_ts(lp_id=1, network=1102)
    print(lp_summary)
    # print(lp_summary.columns)
    print("-----------------------------------")
    # print(data_server.exchange_rate.get_cspr_price(block_number='latest'))
    print("-----------------------------------")
    # snapshot = data_server.lp_summary.get_lp_summary(1)
    # print(snapshot)         #['open_timestamp_utc'], snapshot['close_timestamp_utc'])
    # data_server.exchange_rate.get_token_price_history_by_id(2)
    print("-----------------------------------")

    # # plot some stuff
    # import matplotlib.pyplot as plt
    # lp_summary.set_index("close_timestamp_utc")[['accumulated_token_0_fees', 'accumulated_token_1_fees']].plot()
    # plt.show()

    # cols_to_plot = [t + '_price' for t in ['open', 'close', 'high', 'low']]
    # eth_price.set_index("open_timestamp_utc")[cols_to_plot].plot()
    # plt.show()

    # close connections
    db.close_all_connections()
