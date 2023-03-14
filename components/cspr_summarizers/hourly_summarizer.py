import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from cspr_summarization.entities.HourlyData import HourlyData
from cspr_summarization.entities.BlockHours import BlockHours
import pandas as pd
from cspr_summarization.services.lp_hourly_summarizer.lp_hourly_summarizer import LpHourlySummarizer
import pytz
from datetime import datetime, timedelta
import logging
import schedule
import time

logging.basicConfig(level=logging.INFO)

def run_hourly_summarizer(start_hour_param = None):

  # Normal hourly run
  if start_hour_param is None:
    try:
      last_hourly_block_timestamp = BlockHours.objects.values('hourly_timestamp_utc').order_by('-hourly_timestamp_utc').first()['hourly_timestamp_utc']
      # try to get the last houly data timestamp
      try:
        last_end_hour = HourlyData.objects.values('close_timestamp_utc').order_by('-close_timestamp_utc').first()['close_timestamp_utc']
      # in case the table is empty (this is possible when the service run for the first time)!
      # then get the min hourly data timestamp (from BlockHours)
      except:
        last_end_hour = BlockHours.objects.values('hourly_timestamp_utc').order_by('hourly_timestamp_utc').first()['hourly_timestamp_utc']
        last_end_hour = last_end_hour - timedelta(hours=1)
    except:
      logging.warning('❌ The service could not be started Please populate BlockHours data before running the service as no data was found on the BlockHours table')
      return

    # Set microseconds, seconds, & minutes to 0
    last_end_hour = last_end_hour.replace(microsecond=0, second=0, minute=0)
    last_hourly_block_timestamp = last_hourly_block_timestamp.replace(microsecond=0, second=0, minute=0)
    # Get the start and end hour
    next_start_hour = last_end_hour
    next_end_hour = (next_start_hour + timedelta(hours=1))
    forced_to_run = False
  # In case we forced the service to run for the `FORCE_RECALCULATE_START_HOUR` env var
  else:
    next_start_hour = start_hour_param
    next_end_hour = (next_start_hour + timedelta(hours=1))
    forced_to_run = True
    # just to make the while condition stops after the first loop
    last_hourly_block_timestamp = next_start_hour - timedelta(hours=1)

  # Already summarized data for this hour 
  if (next_start_hour >= last_hourly_block_timestamp) and (not forced_to_run):
    logging.info(f'✅ Hourly Summarization has already been run for the time range: {next_start_hour} - {next_end_hour}')

  # While not done with all the missed past hours Do ...
  while (last_hourly_block_timestamp > next_start_hour) or (forced_to_run):

    summarizer = LpHourlySummarizer(next_start_hour, next_end_hour)
    # Initilize Data (all column at 0)
    summarizer.init_hourly_data()
    logging.info(f'🧮 Hourly Summarization started {next_start_hour} - {next_end_hour}...')

    # At least one block on the last hour
    if len(summarizer.last_hour_block_numbers) > 0 :
      logging.info(f'\t Sync Summarizing data...')
      summarizer.sync_consumer()
      logging.info(f'\t Mint Summarizing data...')
      summarizer.mint_consumer()
      logging.info(f'\t Burn Summarizing data...')
      summarizer.burn_consumer()
      logging.info(f'\t Swap Summarizing data...')
      summarizer.swap_consumer()
      logging.info(f'\t Clost lp token Summarizing data...')
      summarizer.close_lp_token_supply_consumer()
      logging.info(f'\t Max Block Summarizing data...')
      summarizer.max_block_consumer()
      logging.info(f'✅ End of Hourly Summarization for time range {next_start_hour} - {next_end_hour}')
    # No block on the last hour
    else:
      logging.info(f'❗️ No blocks have been created for the time range {next_start_hour} - {next_end_hour}')

    #
    next_start_hour = (next_start_hour + timedelta(hours=1))
    next_end_hour = (next_start_hour + timedelta(hours=1))
    # make sure that the FORCE Summarization run only one time
    forced_to_run = False
    

if __name__ == '__main__':
  logging.info('🚀 Hourly Summarization service started 🚀')

  force_start_hour = os.getenv('FORCE_RECALCULATE_START_HOUR')
  if(force_start_hour is not None and force_start_hour != '' ):
    logging.info(f'🎩 Summarization forced to run for the starting hour: {force_start_hour}')
    try:
      start_hour = datetime.strptime(force_start_hour, '%Y-%m-%d %H:%M %z')
      run_hourly_summarizer(start_hour_param=start_hour)
    except Exception as e:
      logging.info(f'❌ Could not force the summarization')
      logging.info(f'\t ❌ the env var `FORCE_RECALCULATE_START_HOUR` should be of format `%Y-%m-%d %H:%M %z`: ')
      logging.info(f'\t\t ❌ Y: Year (example: 2023)')
      logging.info(f'\t\t ❌ m: Month (example: 02)')
      logging.info(f'\t\t ❌ d: Day (example: 12)')
      logging.info(f'\t\t ❌ H: Hour (exmple: 18)')
      logging.info(f'\t\t ❌ M: Minutes (example: 00)')
      logging.info(f'\t\t ❌ z: Timezone (example: -6:00, which means CET -6 hours)')
      logging.info(f'\t ❌ Example of a valid starting hour: 2023-02-19 10:00 -06:00')



  schedule.every(10).seconds.do(run_hourly_summarizer)
  while True:
      schedule.run_pending()
      time.sleep(1)