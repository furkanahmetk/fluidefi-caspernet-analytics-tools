from cspr_summarization.entities.Blocks import Blocks
from cspr_summarization.entities.BlockHours import BlockHours
from cspr_summarization.entities.UniswapV2Pair import UniswapV2Pair as AllPairs
from cspr_summarization.entities.PairCreatedEvent import PairCreatedEvent
from cspr_summarization.entities.PairBurnEvent import PairBurnEvent
from cspr_summarization.entities.PairMintEvent import PairMintEvent
from cspr_summarization.entities.PairSwapEvent import PairSwapEvent
from cspr_summarization.entities.PairSyncEvent import PairSyncEvent
from cspr_summarization.entities.TokenTotalSupply import TokenTotalSupply
from cspr_summarization.entities.HourlyData import HourlyData


import pandas as pd
import numpy as np
from decimal import Decimal
from django.db.models import F
from django.db import IntegrityError
import logging

logging.basicConfig(level=logging.INFO)

class LpHourlySummarizer:
  
  def __init__(self, start_hour, end_hour):
    self.start_hour = start_hour
    self.end_hour = end_hour
    # Fetch the last hour blocks
    blocks = Blocks.objects \
      .filter(timestamp_utc__gte=self.start_hour, timestamp_utc__lt= self.end_hour) \
      .values('block_number', 'timestamp_utc').order_by('-timestamp_utc')
    self.last_hour_block_numbers = pd.DataFrame.from_records(blocks)
    all_pairs = AllPairs.objects.values('id', 'contract_address', 'token0_decimals', 'token1_decimals', 'token0_address', 'token1_address')
    self.all_pairs = pd.DataFrame.from_records(all_pairs)
  
  '''
  # create a record for each pair, with all values at zero
  '''
  def init_hourly_data(self):
    for index, pair in self.all_pairs.iterrows():
      try:
        hourly_data = HourlyData(pair['contract_address'], self.start_hour, self.end_hour)
        hourly_data.save()
      except IntegrityError:
        hourly_data = HourlyData.objects.get(address=pair['contract_address'], open_timestamp_utc=self.start_hour, close_timestamp_utc=self.end_hour)
        HourlyData.objects \
            .filter(address=pair['contract_address'], open_timestamp_utc=self.start_hour, close_timestamp_utc=self.end_hour) \
            .update(close_reserves_0=0 , close_reserves_1= 0, num_swaps_0= 0, num_swaps_1= 0, num_mints= 0, num_burns= 0, \
                    mints_0= 0, mints_1= 0, burns_0= 0, burns_1= 0, volume_0= 0, volume_1= 0, max_block= 0, close_lp_token_supply= 0)
  
  '''
  # SyncEvents Summarization
  '''
  def sync_consumer(self):
    df_sync = self.sync_finder(self.last_hour_block_numbers['block_number'].values)
    # Sync summarization
    if len(df_sync) > 0:
      close_reserves = self.sync_summarizer(df_sync)
      # save result to DB (update rows)
      self.sync_saver(close_reserves)
    else:
      logging.warning('No sync event on the last hour')
  
  '''
  # MintEvents Summarization 
  '''
  def mint_consumer(self):
    df_mints = self.mint_finder(self.last_hour_block_numbers['block_number'].values)
    # mints_sum_result
    if len(df_mints) > 0:
      mints_sum_result = self.mint_summarizer(df_mints)
      self.mint_saver(mints_sum_result)
    else:
      logging.info('No mint event on the last hour')

  '''
  # BurnEvents Summarization 
  '''
  def burn_consumer(self):
    df_burns = self.burn_finder(self.last_hour_block_numbers['block_number'].values)
    if len(df_burns) > 0:
      # burns_sum_result
      burns_sum_result = self.burn_summarizer(df_burns)
      self.burn_saver(burns_sum_result)
    else:
      logging.info('No burn event on the last hour')
  
  '''
  # SwapEvents Summarization
  '''
  def swap_consumer(self):
    df_swaps = self.swap_finder(self.last_hour_block_numbers['block_number'].values)
    if len(df_swaps) > 0:
      # swap_sum_result
      swap_sum_result = self.swap_summarizer(df_swaps)
      self.swap_saver(swap_sum_result)
    else:
      logging.info('No swap event on the last hour')
  
  '''
  # Close lp token supply
  '''
  def close_lp_token_supply_consumer(self):
    df_token_supply = self.lp_token_supply_finder()
    if len(df_token_supply) > 0:
      close_total_supply = self.lp_token_supply_summarizer(df_token_supply)
      self.lp_token_supply_saver(close_total_supply)
    else:
      logging.info('No data found on the TokenTotalSupply table')

  '''
  # Update Max_block in HourlyData
  '''
  def max_block_consumer(self):
    max_block = self.max_block_finder(self.start_hour, self.end_hour)
    self.max_block_saver(max_block, self.start_hour, self.end_hour)
  

  # =================================================================
  #                             Setters
  # =================================================================

  '''
  # setter needed for tests  
  '''
  def set_last_hour_block_numbers(self, last_hour_block_numbers):
    self.last_hour_block_numbers = last_hour_block_numbers
  
  '''
  # setter needed for tests  
  '''
  def set_all_airs(self, all_pairs):
    self.all_pairs = all_pairs
  
  # =================================================================
  #                           End Setters
  # =================================================================
  

  # =================================================================
  #                 Sync Summarization methods
  # =================================================================
    
  '''
  # return sync events where sync.block_number in block_numbers arg 
  '''
  def sync_finder(self, block_numbers):
    try:
      sync_table = PairSyncEvent.objects.using('default') \
        .filter(block_number__in=block_numbers) \
        .values('id', 'address','block_number', 'reserve0', 'reserve1')

      df_sync = pd.DataFrame.from_records(sync_table)
      return df_sync
    except:
      logging.error('Error occurred while trying to fetch pair sync events from DB')
      return None
  
  '''
  # return sync events summarized 
  '''
  def sync_summarizer(self, df_sync):
    try:
      # group by address and get reserve0 and reserve1 for the max block_number of each address
      close_reserves = df_sync.loc[df_sync.groupby("address")["block_number"].idxmax()]
      return close_reserves
    except:
     logging.error('Error occurred while summarazing sync data')
     return None
  
  '''
  # Update DB
  '''
  def sync_saver(self, close_reserves):
    try:
      for key, item in close_reserves.iterrows():    
      # Updte DB rows
        HourlyData.objects.using('writer') \
          .filter(address=item['address'], open_timestamp_utc=self.start_hour) \
          .update(close_reserves_0=item['reserve0'], close_reserves_1=item['reserve1'])

    except:
      logging.error('Error occured while saving sync summarization results to DB')

  # =================================================================
  #                End Sync Summarization methods
  # =================================================================

  # =================================================================
  #                 Mint Summarization methods
  # =================================================================
    
  '''
  # return mint events where mint_event.block_number in block_numbers arg
  '''
  def mint_finder(self, block_numbers):
    try: 
      mint_table = PairMintEvent.objects.using('default') \
        .filter(block_number__in=block_numbers) \
        .values('id', 'address', 'block_number', 'amount0', 'amount1')#
      df_mint = pd.DataFrame.from_records(mint_table)
      return df_mint
    except:
      logging.error('Error occurred while trying to fetch pair mint events from DB')
      return None
  
  '''
  # return mint events summarized
  '''
  def mint_summarizer(self, df_mints):
    try: 
      mints_sum_result = pd.DataFrame({'num_mints':[], 'mints_0': [], 'mints_1': []})
      # loop through addresses within df_mints
      for index, pair in df_mints.iterrows():
        if pair['address'] in  mints_sum_result.index:
          mint_sum = mints_sum_result.loc[pair['address']]
          mint0 = Decimal(int(np.sum([mint_sum['mints_0'], pair['amount0']])))
          mint1 = Decimal(int(np.sum([mint_sum['mints_1'], pair['amount1']])))
          num_mints = mint_sum['num_mints'] + 1
          mints_sum_result.loc[pair['address']] = [num_mints, mint0, mint1]
        else:
          mints_sum_result.loc[pair['address']] = [1, pair['amount0'], pair['amount1']]
      
      return mints_sum_result
    except:
      logging.error('Error occurred while summarazing mint data')
      return None
  
  '''
  # Update DB 
  '''
  def mint_saver(self, mints_result):
    try:
      for address, item in mints_result.iterrows():
        HourlyData.objects.using('writer') \
          .filter(address=address, open_timestamp_utc=self.start_hour) \
          .update(num_mints=item['num_mints'], mints_0=item['mints_0'], mints_1=item['mints_1'])
    except:
      logging.error('Error occurred while saving mint summarization results to DB')

  # =================================================================
  #                 End Mint Summarization methods
  # =================================================================

  # =================================================================
  #                 Burn Summarization methods
  # =================================================================

  '''
  # return burn event where burn_event.block_number in block_numbers arg
  '''
  def burn_finder(self, block_numbers):
    try:
      burn_table = PairBurnEvent.objects.using('default') \
        .filter(block_number__in=block_numbers) \
        .values('id', 'address', 'block_number', 'amount0', 'amount1')
      df_burn = pd.DataFrame.from_records(burn_table)

      return df_burn
    except:
      logging.error('Error occurred while trying to fetch pair burn events from DB')
      return None
  
  '''
  # return burn events summarized
  '''
  def burn_summarizer(self, df_burns):
    try:
      burns_sum_result = pd.DataFrame({'num_burns':[], 'burns_0': [], 'burns_1': []})
      # loop through addresses within df_burn
      for index, pair in df_burns.iterrows():
        if pair['address'] in  burns_sum_result.index:
          my_sum = burns_sum_result.loc[pair['address']]
          burn0 = Decimal(int(np.sum([my_sum['burns_0'], pair['amount0']])))
          burn1 = Decimal(int(np.sum([my_sum['burns_1'], pair['amount1']])))
          num_burns = my_sum['num_burns'] + 1
          burns_sum_result.loc[pair['address']] = [num_burns, burn0, burn1]
        else:
          burns_sum_result.loc[pair['address']] = [1, pair['amount0'], pair['amount1']]
      
      return burns_sum_result
    except:
      logging.error('Error occurred while summarizing burn data')
      return None
  
  '''
  # update DB
  '''
  def burn_saver(self, burns_result):
    try:
      for address, item in burns_result.iterrows():
        HourlyData.objects.using('writer') \
          .filter(address=address, open_timestamp_utc=self.start_hour) \
          .update(num_burns=item['num_burns'], burns_0=item['burns_0'], burns_1=item['burns_1'])
    except:
      logging.error('Error occurred while trying to save burns summarization results to DB')

  # =================================================================
  #                 End Burn Summarization methods
  # =================================================================

  # =================================================================
  #                 Swap Summarization methods
  # =================================================================  
  
  '''
  # return swap event where burn_event.block_number in block_numbers arg
  '''
  def swap_finder(self, block_numbers):
    try: 
      swaps_table = PairSwapEvent.objects.using('default') \
        .filter(block_number__in=block_numbers) \
        .values('id', 'address', 'block_number', 'amount0_in', 'amount0_out', 'amount1_in', 'amount1_out')
      df_swaps = pd.DataFrame.from_records(swaps_table)

      return df_swaps
    except:
      logging.error('Error occurred while trying to fetch swap events from DB')
      return None
  
  '''
  # return swap events summarized
  '''
  def swap_summarizer(self, df_swaps):
    try:
      # swap_sum_result
      swap_sum_result = pd.DataFrame({'num_swaps_0':[], 'num_swaps_1':[], 'amount0_in':[], 'amount0_out':[], 'amount1_in':[], 'amount1_out':[], 'volume_0':[], 'volume_1':[]})
      # aggregate with group_by pair
      for index, item in df_swaps.iterrows():
        if item['address'] in swap_sum_result.index:
          my_swap = swap_sum_result.loc[item['address']]
          num_swaps_0 = my_swap['num_swaps_0'] + 1 if (item['amount0_in'] > 0 or item['amount0_out']>0) else my_swap['num_swaps_0']
          num_swaps_1 = my_swap['num_swaps_1'] + 1 if (item['amount1_in'] > 0 or item['amount1_out']>0) else my_swap['num_swaps_1']
          amount0_in = Decimal(int(np.sum([my_swap['amount0_in'], item['amount0_in']])))
          amount0_out = Decimal(int(np.sum([my_swap['amount0_out'], item['amount0_out']])))
          amount1_in = Decimal(int(np.sum([my_swap['amount1_in'], item['amount1_in']])))
          amount1_out = Decimal(int(np.sum([my_swap['amount1_out'], item['amount1_out']])))
          swap_sum_result.loc[item['address']] = [num_swaps_0, num_swaps_1, amount0_in, amount0_out, amount1_in, amount1_out, 0, 0]
        else: 
          swap_sum_result.loc[item['address']] = [1, 1, item['amount0_in'], item['amount0_out'], item['amount1_in'], item['amount1_out'], 0, 0]
      # update Volumes ( |amount0_in - amount1_in| )
      for address, item in swap_sum_result.iterrows():
        swap_sum_result.loc[address, 'volume_0'] = Decimal(int(np.abs(item['amount0_in'] - item['amount0_out'])))
        swap_sum_result.loc[address, 'volume_1'] = Decimal(int(np.abs(item['amount1_in'] - item['amount1_out'])))
      
      return swap_sum_result[['num_swaps_0', 'num_swaps_1', 'volume_0', 'volume_1']]
    except:
     logging.error('Error occurred while summarizing swap events')
     return None

  '''
  # update DB
  '''
  def swap_saver(self, swap_result):
    try:
      # update DB
      for address, item in swap_result.iterrows():
        HourlyData.objects.using('writer') \
          .filter(address=address, open_timestamp_utc=self.start_hour) \
          .update(num_swaps_0=item['num_swaps_0'], num_swaps_1=item['num_swaps_1'], volume_0=item['volume_0'], volume_1=item['volume_1'])
    except:
      logging.error('Error occurred while trying to save swaps summarization results to DB')
  
  # =================================================================
  #                 End Swap Summarization methods
  # =================================================================

  # =================================================================
  #                 Close lp token supply methods
  # =================================================================

  '''
  # return token total supply rows
  '''
  def lp_token_supply_finder(self):
    try:
      token_total_supply_table = TokenTotalSupply.objects.using('default').values()
      df_token_supply = pd.DataFrame.from_records(token_total_supply_table)

      return df_token_supply
    except:
      logging.error('Error occurred while trying fo fetch token_total_supply rows from DB')
      return None
  
  '''
  # return close lp token supply for each token_address
  '''
  def lp_token_supply_summarizer(self, df_token_supply):
    try: 
      close_total_supply = df_token_supply.loc[df_token_supply.groupby("token_address")["block_number"].idxmax()]
      return close_total_supply
    except:
      logging.error('Error occurred while summarizing lp_supply_token data')
      return None
  
  '''
  # save max_lp_token_supply to db
  '''
  def lp_token_supply_saver(self, close_total_supply):
    try:
      for key, item in close_total_supply.iterrows():
        HourlyData.objects.using('writer') \
          .filter(address=item['token_address'], open_timestamp_utc=self.start_hour) \
          .update(close_lp_token_supply=item['total_supply'])
    except:
      logging.error('Error occurred while trying to save lp_supply_token to DB')

  # =================================================================
  #                end Close lp token supply methods
  # =================================================================

  # =================================================================
  #                       Max_block methods
  # =================================================================

  '''
  # max block finder
  '''
  def max_block_finder(self, start_hour, end_hour):
    try:
      max_block = BlockHours.objects.using('default') \
      .filter(block_timestamp_utc__range=(self.start_hour, self.end_hour)) \
      .values('block_number').order_by('-block_timestamp_utc').first()

      return max_block['block_number']
    except:
      logging.error('Error occurred while trying to fetch max_block from DB')
      return None
  
  '''
  # max block saver
  '''
  def max_block_saver(self, max_block, start_hour, end_hour):
    try:
      HourlyData.objects.using('writer') \
        .filter(open_timestamp_utc=start_hour, close_timestamp_utc=end_hour) \
        .update(max_block=max_block)
    except:
      logging.error('Error occurred while trying to save max_block to DB')
  # =================================================================
  #                       end Max_block methods
  # =================================================================
  
    