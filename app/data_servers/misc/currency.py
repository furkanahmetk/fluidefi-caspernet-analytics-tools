import pandas as pd


class CurrencyAnalytics:
    def __init__(self, prod_us1_conn, fl_agg_conn, exchange_rate_server):
        self.prod_us1_conn = prod_us1_conn
        self.fl_agg_conn = fl_agg_conn
        self.exchange_rate_server = exchange_rate_server
        self.start_date = None
        self.end_date = None

    def set_date_range(self, start_date, end_date):
        # remove timezone information and convert to datetime
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=None)
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=None)
