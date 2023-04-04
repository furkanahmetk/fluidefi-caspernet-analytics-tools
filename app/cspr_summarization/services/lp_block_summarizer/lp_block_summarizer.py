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
logging.basicConfig(level=logging.WARN)
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
    Finds all of the pairs stored in the datastore at the current block height and returns the pair, blockNumber, and timestamp as a dataframe
    '''
    def allPairsFinder(self):
        try:
            all_pairs_table = UniswapV2Pair.objects.using('default').filter(first_mint_event_block_number__lte=self.blockNumber).values('contract_address')
            df = pd.DataFrame.from_records(all_pairs_table)
            df = df.rename(columns={'contract_address': 'address'})
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
            raw_pair_sync_event_table = PairSyncEvent.objects.using('default').filter(block_number__lte=self.blockNumber, address=address).values('address', 'reserve0', 'reserve1').order_by('-block_number').first()
            if not raw_pair_sync_event_table:
                return None
            df = pd.DataFrame.from_dict([raw_pair_sync_event_table])
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
        dfs = []
        for address in self.pairs['address']:
            try:
                df = self.latestPairSyncEventFinder(address)
                if df is not None:
                    dfs.append(df)
            except:
                logging.warn(f"Failed to find sync event for address {address}")
        if not dfs:
            return self.pairs
        else:
            merged_df = pd.concat(dfs)
        return pd.merge(self.pairs, merged_df, on='address', how='outer')

    '''
    Finds the mint event of the pair at the current height and returns the number of mint events, amount added in token0, and token1 for the specific pair as a dataframe
    '''
    def pairMintEventFinder(self, address):
        try:
            raw_pair_mint_event_table = PairMintEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('address','amount0', 'amount1')
            if not raw_pair_mint_event_table:
                logging.info(f'No mint events for pair {address}')
                data = [[address, 0, 0, 0]]
                cols = ['address','num_mints', 'mints_0', 'mints_1']
                df = pd.DataFrame(data, columns=cols)
                return df
            df_raw_mints = pd.DataFrame.from_records(raw_pair_mint_event_table)
            num_mints = len(df_raw_mints)
            mints_0 = Decimal(np.sum(df_raw_mints['amount0'].to_numpy()))
            mints_1 = Decimal(np.sum(df_raw_mints['amount1'].to_numpy()))
            data = [[address, num_mints, mints_0, mints_1]]
            cols = ['address','num_mints', 'mints_0', 'mints_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding mint event for pair at block: : %s', str(e))
            return None
        
 
    '''
    Checks the datastore for any recrods of mint events for each pair, and concats the two dataframes if any mint record of the pair was found. 
    '''
    def pairMintEventChecker(self):
        if self.syncs.empty:
            return None
        dfs = []
        for address in self.syncs['address']:
            try:
                df = self.pairMintEventFinder(address)
                if df is not None:
                    dfs.append(df)
            except:
                logging.warn(f"Failed to find mint event for address {address}")
        if not dfs:
            return self.syncs
        else:
            merged_df = pd.concat(dfs)
        return pd.merge(self.syncs, merged_df, on='address', how='outer')
    
    '''
    Finds the burn event of the pair at the current height and returns the number of mint events, amount removed from token0, and token1 for the specific pair as a dataframe
    '''
    def pairBurnEventFinder(self, address):
        try:
            raw_pair_burn_event_table = PairBurnEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('address', 'amount0', 'amount1')
            if not raw_pair_burn_event_table:
                logging.info(f'No burn events for pair with address {address}')
                data = [[address, 0, 0, 0]]
                cols = ['address', 'num_burns', 'burns_0', 'burns_1']
                df = pd.DataFrame(data, columns=cols)
                return df
            df_raw_burns = pd.DataFrame.from_records(raw_pair_burn_event_table)
            num_burns = len(df_raw_burns)
            burns_0 = Decimal(np.sum(df_raw_burns['amount0'].to_numpy()))
            burns_1 = Decimal(np.sum(df_raw_burns['amount1'].to_numpy()))
            data = [[address, num_burns, burns_0, burns_1]]
            cols = ['address', 'num_burns', 'burns_0', 'burns_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding burn event for pair at block: : %s', str(e))
            return None
    
    '''
    Checks the datastore for any recrods of burn events for each pair, and concats the two dataframes if any burn record of the pair was found. 
    '''
    def pairBurnEventChecker(self):
        if self.mints.empty:
            return None
        dfs = []
        for address in self.mints['address']:
            try:
                df = self.pairBurnEventFinder(address)
                if df is not None:
                    dfs.append(df)
            except:
                logging.warn(f"Failed to find burn event for address {address}")
        if not dfs:
            return self.mints
        else:
            merged_df = pd.concat(dfs)
        return pd.merge(self.mints, merged_df, on='address', how='outer')


    '''
    Finds swap events of the pair at the current height and returns amount0_in, amount0_out, amount1_in, amount1_out as a dataframe
    '''
    def pairSwapEventFinder(self, address):
        try:
            raw_pair_swap_event_table = PairSwapEvent.objects.using('default').filter(block_number=self.blockNumber, address=address).values('address','amount0_in', 'amount0_out', 'amount1_in', 'amount1_out')
            if not raw_pair_swap_event_table:
                logging.info(f'No swap events for pair with address {address}')
                data = [[address, 0, 0, 0, 0]]
                cols = ['address', 'num_swaps_0', 'num_swaps_1', 'volume_0', 'volume_1']
                df = pd.DataFrame(data, columns=cols)
                return df
            df_raw_swaps = pd.DataFrame.from_records(raw_pair_swap_event_table)
            num_swaps_0 = df_raw_swaps[(df_raw_swaps['amount0_in'] > 0) | (df_raw_swaps['amount0_out'] > 0)]['amount0_in'].count()
            num_swaps_1 = df_raw_swaps[(df_raw_swaps['amount1_in'] > 0) | (df_raw_swaps['amount1_out'] > 0)]['amount1_in'].count()
            volume_0 = Decimal(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_in'] > 0, 'amount0_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_out'] > 0, 'amount0_out'].to_numpy())))
            volume_1 = Decimal(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_in'] > 0, 'amount1_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_out'] > 0, 'amount1_out'].to_numpy())))
            data = [[address, num_swaps_0, num_swaps_1, volume_0, volume_1]]
            cols = ['address', 'num_swaps_0', 'num_swaps_1', 'volume_0', 'volume_1']
            df = pd.DataFrame(data, columns=cols)
            return df
        except Exception as e:
            logging.error('Error occurred while finding swap events for block: : %s', str(e))
            return None
        
    
    '''
    Checks the datastore for any recrods of burn events for each pair, and concats the two dataframes if any burn record of the pair was found. 
    '''
    def pairSwapEventChecker(self):
        if self.burns.empty:
            return None
        dfs = []
        for address in self.burns['address']:
            try:
                df = self.pairSwapEventFinder(address)
                if df is not None:
                    dfs.append(df)
            except:
                logging.warn(f"Failed to find swap event for address {address}")
        if not dfs:
            return self.burns
        else:
            merged_df = pd.concat(dfs)
        return pd.merge(self.burns, merged_df, on='address', how='outer')
    
    '''
    Finds the latest token total supply record of the pair at the current height and returns the amount as a dataframe
    '''
    def latestTokenTotalSupplyFinder(self, address):
        try:
            token_total_supply_table = TokenTotalSupply.objects.using('default').filter(block_number__lte=self.blockNumber, token_address=address).values('token_address', 'total_supply').order_by('-block_number').first()
            if not token_total_supply_table:
                data = [[address, 0]]
                cols = ['address', 'total_supply']
                df = pd.DataFrame(data, columns=cols)
                return df
            df = pd.DataFrame.from_records([token_total_supply_table])
            df = df.rename(columns={'token_address': 'address'})
            return df
        except Exception as e:
            logging.error('Error occurred while finding the token total supply for pair: {address}', str(e))
            return None
        
    '''
    Checks the datastore for the latest token total supply record for each pair, and concats the two dataframes. 
    '''
    def tokenTotalSupplyChecker(self):
        if self.swaps.empty:
            return None
        dfs = []
        for address in self.swaps['address']:
            try:
                df = self.latestTokenTotalSupplyFinder(address)
                if df is not None:
                    dfs.append(df)
            except:
                logging.warn(f"Failed to find latest token total supply for address {address}")
        if not dfs:
            return self.swaps
        else:
            merged_df = pd.concat(dfs)
        return pd.merge(self.swaps, merged_df, on='address', how='outer')
    
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
        except Exception as e:
            logging.info(f"Couldn't save block_summary for {row} %s", str(e))