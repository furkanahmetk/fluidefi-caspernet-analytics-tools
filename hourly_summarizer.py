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
from cspr_summarization.services.lp_hourly_summarizer import LpHourlySummarizer
import pytz
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)

last_hourly_block_timestamp = BlockHours.objects.values('hourly_timestamp_utc').order_by('-hourly_timestamp_utc').first()['hourly_timestamp_utc']

# try to get the last houly data timestamp
try:
  last_end_hour = HourlyData.objects.values('close_timestamp_utc').order_by('-close_timestamp_utc').first()['close_timestamp_utc']
# in case the table is empty!
# then get the min hourly data timestamp (from BlockHours)
except:
  last_end_hour = BlockHours.objects.values('hourly_timestamp_utc').order_by('hourly_timestamp_utc').first()['hourly_timestamp_utc']

# Set microseconds, seconds, & minutes to 0
last_end_hour = last_end_hour.replace(microsecond=0, second=0, minute=0)
last_hourly_block_timestamp = last_hourly_block_timestamp.replace(microsecond=0, second=0, minute=0)

# Get the start and end hour
next_start_hour = last_end_hour
next_end_hour = (next_start_hour + timedelta(hours=1))

# Already summarized data for this hour
if next_start_hour > last_hourly_block_timestamp:
  print(f'All good for: {next_start_hour} - {next_end_hour}')
  exit(0)

# While not done with all the missed past hours Do ...
while last_hourly_block_timestamp >= next_start_hour:

  summarizer = LpHourlySummarizer(next_start_hour, next_end_hour)
  # Initilize Data (all column at 0)
  summarizer.init_hourly_data()
  logging.info(f'Summarization started {next_start_hour} - {next_end_hour}...')

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
    logging.info(f'\t End')
  # No block on the last hour
  else:
    logging.info(f'No blocks have been created between {next_start_hour} - {next_end_hour}')

  #
  next_start_hour = (next_start_hour + timedelta(hours=1))
  next_end_hour = (next_start_hour + timedelta(hours=1))
  

