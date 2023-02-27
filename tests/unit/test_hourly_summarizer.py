import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

import unittest
import pandas as pd
from decimal import Decimal
import pytz
from datetime import datetime, timedelta


from cspr_summarization.services.lp_hourly_summarizer import LpHourlySummarizer


class TestHourlySummarizer(unittest.TestCase):

  # Test sync summarizer
  def test_sync_summarizer(self):
    timestamp_string = '2023-01-09 09:55:39.648000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    start_hour = timestamp_obj.astimezone(pytz.UTC)

    timestamp_string = '2023-01-12 01:47:19.936000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    end_hour = timestamp_obj.astimezone(pytz.UTC)

    hourly_summarizer = LpHourlySummarizer(start_hour, end_hour)
    df_sync = pd.DataFrame({
      'id': [1, 2, 3, 4],
      'address':      ['cf56e3', 'cf56e3', '800dee', '800dee'],
      'block_number': [1398801, 1398802, 1398803, 1398804],
      'reserve0':     [144100081137, 143967281437, 1000000000, 59],
      'reserve1':     [919041928425877, 910434567551373, 919041928425879, 910434567551375]
    })

    expected_success_result = pd.DataFrame({
      'id': [4, 2],
      'address': ['800dee','cf56e3'],
      'block_number': [1398804, 1398802],
      'reserve0': [59, 143967281437],
      'reserve1': [910434567551375, 910434567551373]
    }, index=[3, 1])

    # get sync summarization data
    df_result = hourly_summarizer.sync_summarizer(df_sync)
    # test result should equal expected result
    self.assertTrue(expected_success_result.equals(df_result))

  # Test mint summarizer
  def test_mint_summarizer(self):
    timestamp_string = '2023-01-09 09:55:39.648000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    start_hour = timestamp_obj.astimezone(pytz.UTC)

    timestamp_string = '2023-01-12 01:47:19.936000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    end_hour = timestamp_obj.astimezone(pytz.UTC)

    hourly_summarizer = LpHourlySummarizer(start_hour, end_hour)
    df_mint = pd.DataFrame({
      'id': [1, 2, 3, 4],
      'address':      ['cf56e3', 'cf56e3', '800dee', '800dee'],
      'block_number': [1398801, 1398802, 1398803, 1398804],
      'amount0':     [144100081137, 143967281437, 1000000000, 59],
      'amount1':     [919041928425877, 910434567551373, 919041928425879, 910434567551375]
    })

    expected_success_result = pd.DataFrame({
      'num_mints': [2, 2],
      'mints_0': [Decimal(288067362574), Decimal(1000000059)],
      'mints_1': [Decimal(1829476495977250), Decimal(1829476495977254)]
    }, index=['cf56e3', '800dee'])

    # get summarized data
    df_result = hourly_summarizer.mint_summarizer(df_mint)
    # test result should equal expected result
    self.assertTrue(expected_success_result.equals(df_result))
  
  # Test burn summarizer
  def test_burn_summarizer(self):
    timestamp_string = '2023-01-09 09:55:39.648000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    start_hour = timestamp_obj.astimezone(pytz.UTC)

    timestamp_string = '2023-01-12 01:47:19.936000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    end_hour = timestamp_obj.astimezone(pytz.UTC)

    hourly_summarizer = LpHourlySummarizer(start_hour, end_hour)
    df_burn = pd.DataFrame({
      'id': [1, 2, 3, 4],
      'address':      ['cf56e3', 'cf56e3', '800dee', '800dee'],
      'block_number': [1398801, 1398802, 1398803, 1398804],
      'amount0':     [144100081137, 143967281437, 1000000000, 59],
      'amount1':     [919041928425877, 910434567551373, 919041928425879, 910434567551375]
    })

    expected_success_result = pd.DataFrame({
      'num_burns': [2, 2],
      'burns_0': [Decimal(288067362574), Decimal(1000000059)],
      'burns_1': [Decimal(1829476495977250), Decimal(1829476495977254)]
    }, index=['cf56e3', '800dee'])

    # get summarized data
    df_result = hourly_summarizer.burn_summarizer(df_burn)
    # test result should equal expected result
    self.assertTrue(expected_success_result.equals(df_result))

  # Test swap summarizer
  def test_swap_summarizer(self):
    timestamp_string = '2023-01-09 09:55:39.648000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    start_hour = timestamp_obj.astimezone(pytz.UTC)

    timestamp_string = '2023-01-12 01:47:19.936000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    end_hour = timestamp_obj.astimezone(pytz.UTC)

    hourly_summarizer = LpHourlySummarizer(start_hour, end_hour)
    df_swap = pd.DataFrame({
      'id': [1, 2, 3, 4],
      'address':      ['cf56e3', 'cf56e3', '800dee', '800dee'],
      'block_number': [1398801, 1398802, 1398803, 1398804],
      'amount0_in':   [100, 10, 200, 40],
      'amount0_out':  [30, 40, 50, 60],
      'amount1_in':   [3000, 100, 7900, 100],
      'amount1_out':  [50, 50, 1000, 1000]
    })

    expected_success_result = pd.DataFrame({
      'num_swaps_0': [2, 2],
      'num_swaps_1': [2, 2],
      'volume_0': [Decimal(40), Decimal(130)],
      'volume_1': [Decimal(3000), Decimal(6000)]
    }, index=['cf56e3', '800dee'])

    # get summarized data
    df_result = hourly_summarizer.swap_summarizer(df_swap)
    # test result should equal expected result
    self.assertTrue(expected_success_result.equals(df_result))
  
  # Test close_lp_token
  def test_close_lp_token(self):
    timestamp_string = '2023-01-09 09:55:39.648000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    start_hour = timestamp_obj.astimezone(pytz.UTC)

    timestamp_string = '2023-01-12 01:47:19.936000 +00:00'
    timestamp_obj = datetime.strptime(timestamp_string, '%Y-%m-%d %H:%M:%S.%f %z')
    end_hour = timestamp_obj.astimezone(pytz.UTC)

    hourly_summarizer = LpHourlySummarizer(start_hour, end_hour)
    df_token_supply = pd.DataFrame({
      'id':             [1, 2, 3, 4],
      'token_address':  ['cf56e3', 'cf56e3', '800dee', '800dee'],
      'block_number':   [1398801, 1398802, 1398803, 1398804],
      'total_supply':   [100, 10, 200, 40]
    })

    expected_success_result = pd.DataFrame({
      'id': [2, 4],
      'token_address': ['800dee', 'cf56e3'],
      'block_number': [1398804, 1398802],
      'total_supply': [Decimal(40), Decimal(10)]
    }, index=[3, 1])

    # get summarized data
    df_result = hourly_summarizer.lp_token_supply_summarizer(df_token_supply)

    # test result should equal expected result
    self.assertEqual(df_result.loc[df_result['token_address'] == '800dee', 'block_number'].values[0], expected_success_result.loc[expected_success_result['token_address'] == '800dee', 'block_number'].values[0])
    self.assertEqual(df_result.loc[df_result['token_address'] == '800dee', 'total_supply'].values[0], expected_success_result.loc[expected_success_result['token_address'] == '800dee', 'total_supply'].values[0])

    self.assertEqual(df_result.loc[df_result['token_address'] == 'cf56e3', 'block_number'].values[0], expected_success_result.loc[expected_success_result['token_address'] == 'cf56e3', 'block_number'].values[0])
    self.assertEqual(df_result.loc[df_result['token_address'] == 'cf56e3', 'total_supply'].values[0], expected_success_result.loc[expected_success_result['token_address'] == 'cf56e3', 'total_supply'].values[0])


if __name__ == '__main__':  
  unittest.main()