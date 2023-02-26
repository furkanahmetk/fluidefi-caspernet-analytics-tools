from cspr_summarization.entities.UniswapV2Pair import UniswapV2Pair
from cspr_summarization.entities.PairSyncEvent import PairSyncEvent
from cspr_summarization.entities.Blocks import Blocks
from cspr_summarization.entities.PairMintEvent import PairMintEvent
from cspr_summarization.entities.PairBurnEvent import PairBurnEvent
from cspr_summarization.entities.PairSwapEvent import PairSwapEvent
from cspr_summarization.entities.TokenTotalSupply import TokenTotalSupply
from cspr_summarization.entities.BlockSummary import BlockSummary

from decimal import Decimal
import pandas as pd
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)

class LPBlockSummarizer:
    def __init__(self, blockNumber):
        self.blockNumber = blockNumber
        self.pairs = self.allPairsFinder()
        self.syncs = self.pairSyncEventChecker()
        self.mints = self.pairMintEventChecker()
        self.burns = self.pairBurnEventChecker()
        self.swaps = self.pairSwapEventChecker()
        self.summary = self.tokenTotalSupplyChecker()
    '''
    Finds the timestamp of the block and returns the timestamp as a scalar value.
    '''
    def blockTimestampFinder(self):
        try:
            block = Blocks.objects.using('default').filter(block_number=self.blockNumber).values('timestamp_utc').first()
            if not block:
                logging.error('No block found for block number %s', self.blockNumber)
                return None
            return block['timestamp_utc']
        except Exception as e:
            logging.error('Error occurred while finding block timestamp for block: %s', str(e))
            return None
        
    '''
    Finds all of the pairs stored in the datastore and returns the pair, blockNumber, and timestamp as a dataframe
    '''
    def allPairsFinder(self):
        try:
            all_pairs_table = UniswapV2Pair.objects.using('default').values_list('contract_address')
            df = pd.DataFrame.from_records(all_pairs_table, columns=['address'])
            df['block_number'] = self.blockNumber
            timestamp = self.blockTimestampFinder()
            if not timestamp:
                return None
            df['block_timestamp_utc'] = timestamp
            return df
        except Exception as e:
            logging.error('Error occurred while finding pairs', str(e))
            return None
        
    
    '''
    Finds the latest pair sync event of the pair at the current height and returns the pair address, reserve0 and reserve1 as a dataframe
    '''
    def latestPairSyncEventFinder(self, address):
        try:
            raw_pair_sync_event_table = PairSyncEvent.objects.using('default').filter(block_number__lte=self.blockNumber, address=address).values('reserve0', 'reserve1')
            df = pd.DataFrame.from_records(raw_pair_sync_event_table, index=[0])
            return df
        except Exception as e:
            logging.error('Error occurred while finding sync event for block: : %s', str(e))
            return None
    
    '''
    Checks the latest sync event for each pair stored in the datastore, and concats the two dataframes if sync record of the pair was found. 
    '''
    def pairSyncEventChecker(self):
        if self.pairs.empty:
            return None
        merged_list = []
        for address in self.pairs['address']:
            try:
                df = self.latestPairSyncEventFinder(address)
                merged_list.append(df)
            except:
                logging.info(f"No record for pair with address of {address}")
        df = pd.concat([self.pairs, *merged_list], axis=1)
        return df

    '''
    Finds the mint event of the pair at the current height and returns the number of mint events, amount added in token0, and token1 for the specific pair as a dataframe
    '''
    def pairMintEventFinder(self, address):
        try:
            raw_pair_mint_event_table = PairMintEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('amount0', 'amount1')
            if not raw_pair_mint_event_table:
                logging.info(f'No mint events for pair {address}')
                return None
            df_raw_mints = pd.DataFrame.from_records(raw_pair_mint_event_table)
            num_mints = len(df_raw_mints)
            mints_0 = Decimal(np.sum(df_raw_mints['amount0'].to_numpy()))
            mints_1 = Decimal(np.sum(df_raw_mints['amount1'].to_numpy()))
            data = [[num_mints, mints_0, mints_1]]
            cols = ['num_mints', 'mints_0', 'mints_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding mint event for pair at block: : %s', str(e))
            return None
        
 
    '''
    Checks the datastore for any recrods of mint events for each pair, and concats the two dataframes if any mint record of the pair was found. 
    '''
    def pairMintEventChecker(self):
        pairs = self.syncs
        merged_list = []
        for address in pairs['address']:
            try:
                df_mints = self.pairMintEventFinder(address)
                merged_list.append(df_mints)
            except:
                logging.info(f"No mint records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    '''
    Finds the burn event of the pair at the current height and returns the number of mint events, amount removed from token0, and token1 for the specific pair as a dataframe
    '''
    def pairBurnEventFinder(self, address):
        try:
            raw_pair_burn_event_table = PairBurnEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('amount0', 'amount1')
            if not raw_pair_burn_event_table:
                logging.info(f'No burn events for pair with address {address}')
                return None
            df_raw_burns = pd.DataFrame.from_records(raw_pair_burn_event_table)
            num_burns = len(df_raw_burns)
            burns_0 = Decimal(np.sum(df_raw_burns['amount0'].to_numpy()))
            burns_1 = Decimal(np.sum(df_raw_burns['amount1'].to_numpy()))
            data = [[num_burns, burns_0, burns_1]]
            cols = ['num_burns', 'burns_0', 'burns_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding burn event for pair at block: : %s', str(e))
            return None
    
    '''
    Checks the datastore for any recrods of burn events for each pair, and concats the two dataframes if any burn record of the pair was found. 
    '''
    def pairBurnEventChecker(self):
        pairs = self.mints
        merged_list = []
        for address in pairs['address']:
            try:
                df_burns = self.pairBurnEventFinder(address)
                merged_list.append(df_burns)
            except:
                logging.info(f"No burn records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df


    '''
    Finds swap events of the pair at the current height and returns amount0_in, amount0_out, amount1_in, amount1_out as a dataframe
    '''
    def pairSwapEventFinder(self, address):
        try:
            raw_pair_swap_event_table = PairSwapEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('amount0_in', 'amount0_out', 'amount1_in', 'amount1_out')
            if not raw_pair_swap_event_table:
                logging.info(f'No swap events for pair with address {address}')
                return None
            df_raw_swaps = pd.DataFrame.from_records(raw_pair_swap_event_table)
            num_swaps_0 = df_raw_swaps[(df_raw_swaps['amount0_in'] > 0) | (df_raw_swaps['amount0_out'] > 0)]['amount0_in'].count()
            num_swaps_1 = df_raw_swaps[(df_raw_swaps['amount1_in'] > 0) | (df_raw_swaps['amount1_out'] > 0)]['amount1_in'].count()
            volume_0 = Decimal(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_in'] > 0, 'amount0_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_out'] > 0, 'amount0_out'].to_numpy())))
            volume_1 = Decimal(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_in'] > 0, 'amount1_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_out'] > 0, 'amount1_out'].to_numpy())))
            data = [[num_swaps_0, num_swaps_1, volume_0, volume_1]]
            cols = ['num_swaps_0', 'num_swaps_1', 'volume_0', 'volume_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding swap events for block: : %s', str(e))
            return None
        
    
    '''
    Checks the datastore for any recrods of burn events for each pair, and concats the two dataframes if any burn record of the pair was found. 
    '''
    def pairSwapEventChecker(self):
        pairs = self.burns
        merged_list = []
        for address in pairs['address']:
            try:
                df_swaps = self.pairSwapEventFinder(address)
                merged_list.append(df_swaps)
            except:
                logging.info(f"No swap records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    '''
    Finds the latest token total supply record of the pair at the current height and returns the amount as a dataframe
    '''
    def latestTokenTotalSupplyFinder(self, address):
        try:
            token_total_supply_table = TokenTotalSupply.objects.using('default').filter(block_number__lte=self.blockNumber, token_address=address).values('total_supply')
            df = pd.DataFrame.from_records(token_total_supply_table, index=[0])
            return df
        except Exception as e:
            logging.error('Error occurred while finding the token total supply for pair: {address}', str(e))
            return None
        
    '''
    Checks the datastore for the latest token total supply record for each pair, and concats the two dataframes. 
    '''
    def tokenTotalSupplyChecker(self):
        pairs = self.swaps
        merged_list = []
        for address in pairs['address']:
            try:
                df_swaps = self.latestTokenTotalSupplyFinder(address)
                merged_list.append(df_swaps)
            except:
                logging.info(f"No token total supply records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    '''
    Cleans up the dataframe and saves to datastore
    '''   
    def summarizer(self):
        df = self.summary
        df.fillna(0, inplace=True)
        columns_to_check = ['total_supply', 'reserve0', 'reserve1', 'num_swaps_0', 'num_swaps_1', 'num_mints', 'num_burns', 'mints_0', 'mints_1', 'burns_0', 'burns_1', 'volume_0', 'volume_1']
        for col in columns_to_check:
            if col not in df.columns:
                df[col] = 0
        try:
            for index, row in df.iterrows():
                block_summary, created_block_summary = BlockSummary.objects.using('writer').update_or_create(
                    address=row['address'],
                    block_number=row['block_number'],
                    defaults=row.to_dict(),
                )
            return block_summary,created_block_summary
        except:
            logging.info(f"Couldn't save block_summary for {row}")