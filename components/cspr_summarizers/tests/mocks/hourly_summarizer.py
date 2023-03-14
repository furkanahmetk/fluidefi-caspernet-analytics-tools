import pandas as pd
import numpy as np
from decimal import Decimal
import logging
from fixtures.block_summarizer import blocks, pairs

logging.basicConfig(level=logging.INFO)

class LpHourlySummarizer:
  
  def __init__(self, start_hour, end_hour):
    self.start_hour = start_hour
    self.end_hour = end_hour
    # Fetch the last hour blocks
    self.last_hour_block_numbers = pd.DataFrame.from_records(blocks)
    all_pairs = pairs


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

  # =================================================================
  #                End Sync Summarization methods
  # =================================================================

  # =================================================================
  #                 Mint Summarization methods
  # =================================================================

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
  
  # =================================================================
  #                 End Mint Summarization methods
  # =================================================================

  # =================================================================
  #                 Burn Summarization methods
  # =================================================================

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

  # =================================================================
  #                 End Burn Summarization methods
  # =================================================================

  # =================================================================
  #                 Swap Summarization methods
  # =================================================================  

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

  # =================================================================
  #                 End Swap Summarization methods
  # =================================================================

  # =================================================================
  #                 Close lp token supply methods
  # =================================================================

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
 
  # =================================================================
  #                end Close lp token supply methods
  # =================================================================
    