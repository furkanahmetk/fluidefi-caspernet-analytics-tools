import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from sqlalchemy import create_engine, text


class DBConnectionManager:
    # Pool size is the maximum number of permanent connections to keep.
    # Temporarily exceeds the set pool_size if no connections are available.
    # The total number of concurrent connections = pool_size + max_overflow.
    # max_overflow=-1       # Unlimited Connections - HAVE NOT TESTED
    def __init__(self, pool_size=35, max_overflow=20):
        self.pool_size = pool_size

        # keep _connections instance variable
        self._connections = []

        # connection strings
        # =============================================
        prod_us1_r_url = f"postgresql://{os.getenv('READ_DB_CONNECTION_USERNAME')}:{os.getenv('READ_DB_CONNECTION_PASSWORD')}@{os.getenv('READ_DB_CONNECTION_HOST')}:{os.getenv('READ_DB_CONNECTION_PORT')}/{os.getenv('READ_DB_CONNECTION_DATABASE')}"
        prod_us1_rw_url = f"postgresql://{os.getenv('WRITE_DB_CONNECTION_USERNAME')}:{os.getenv('WRITE_DB_CONNECTION_PASSWORD')}@{os.getenv('WRITE_DB_CONNECTION_HOST')}:{os.getenv('WRITE_DB_CONNECTION_PORT')}/{os.getenv('WRITE_DB_CONNECTION_DATABASE')}"
        fl_agg_cspr_r_url = f"postgresql://{os.getenv('READ_DB_CONNECTION_USERNAME')}:{os.getenv('READ_DB_CONNECTION_PASSWORD')}@{os.getenv('READ_DB_CONNECTION_HOST')}:{os.getenv('READ_DB_CONNECTION_PORT')}/{os.getenv('READ_DB_CONNECTION_DATABASE')}"
        fl_agg_cspr_rw_url = f"postgresql://{os.getenv('WRITE_DB_CONNECTION_USERNAME')}:{os.getenv('WRITE_DB_CONNECTION_PASSWORD')}@{os.getenv('WRITE_DB_CONNECTION_HOST')}:{os.getenv('WRITE_DB_CONNECTION_PORT')}/{os.getenv('WRITE_DB_CONNECTION_DATABASE')}"

        # connection instances
        # =============================================
        self._prod_us1_eng_r = create_engine(
            f'{prod_us1_r_url}',
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True, future=True
        )

        self._prod_us1_eng_rw = create_engine(
            f'{prod_us1_rw_url}',
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True, future=True
        )

        self._fl_agg_cspr_eng_r = create_engine(
            f'{fl_agg_cspr_r_url}',
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True, future=True
        )

        self._fl_agg_cspr_eng_rw = create_engine(
            f'{fl_agg_cspr_rw_url}',
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True, future=True
        )

    def get_connection(self, db_name, mode='rw'):
        """
        Get A DBAPI. When done, please close by calling method .close()
        :param db_name: prod_us1 or fl_agg_univ2
        :param mode: r for read-only or rw for read and write
        :return: DBAPI
        """
        assert db_name in ['prod_us1', 'postgres'], "Invalid/Unsupported DB name"
        assert mode in ['r', 'rw'], "Invalid/Unsupported mode"

        # Create a SQLAlchemy Engine and connection
        if db_name == 'prod_us1':
            if mode == 'r':
                connection = self._prod_us1_eng_r.connect()
            elif mode == 'rw':
                connection = self._prod_us1_eng_rw.connect()
        elif db_name == 'postgres':
            if mode == 'r':
                connection = self._fl_agg_cspr_eng_r.connect()
            elif mode == 'rw':
                connection = self._fl_agg_cspr_eng_rw.connect()

        self._connections.append(connection)
        return connection

    def close_all_connections(self):
        for connection in self._connections:
            connection.close()

    def __del__(self):
        """
        Closes the DB automatically when the program ends
        """
        self.close_all_connections()


if __name__ == "__main__":
    # How to use:
    db = DBConnectionManager()          # Instantiate the object

    # These are sqlalchemy.engine.base.Connection object type. Similar to psycopg2
    prod_us1_conn = db.get_connection("postgres", "r")
    fl_agg_cspr_conn = db.get_connection("postgres", "r")

    # Some db operations...
    num_lps = fl_agg_cspr_conn.execute(text("SELECT count(*) FROM all_pairs")).fetchone()[0]
    num_tokens = prod_us1_conn.execute(text("SELECT count(*) FROM erc20_token")).fetchone()[0]
    print(f"FLUIDEFI is CONNECTED & found {num_lps} liquidity pools & {num_tokens} ERC-20 tokens.")

    # Close connections
    prod_us1_conn.close()
    fl_agg_cspr_conn.close()
