"""
Set of helpful functions
"""

import pandas as pd
from sqlalchemy import text

def load_blocks_range_df(fl_agg_conn, start_date) -> pd.DataFrame:
    """
    Provides the starting and ending block for each hour

    @param fl_agg_conn: read connection
    @param start_date: Starting date for the blocks range
    @return: dataframe where index is a timestamp and columns are start and end block
    """
    query = f"""
        SELECT 
            block_number + 1 as start_block,
            hourly_timestamp_utc as timestamp_utc
        FROM block_hours
        WHERE hourly_timestamp_utc >= '{start_date}'
        ORDER BY hourly_timestamp_utc ASC
    """
    blocks = pd.read_sql(text(query), fl_agg_conn, parse_dates=True, index_col='timestamp_utc')
    blocks['end_block'] = blocks['start_block'].shift(-1) - 1
    return blocks.iloc[:-1].astype(int)