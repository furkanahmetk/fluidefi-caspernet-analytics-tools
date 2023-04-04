import sys
sys.path.insert(0, "../")
from fixtures.block_summarizer import blocks, pairs, sync_events, mint_events, burn_events, swap_events, total_supply
import pandas as pd
import numpy as np
from decimal import Decimal

class MockBlockSummarizer:
    def __init__(self, blockNumber):
        self.blockNumber = blockNumber
        self.pairs = self.allPairsFinder()
        self.syncs = self.pairSyncEventChecker()
        self.mints = self.pairMintEventChecker()
        self.burns = self.pairBurnEventChecker()
        self.swaps = self.pairSwapEventChecker()
        self.summary = self.tokenTotalSupplyChecker()

    def blockTimestampFinder(self):
        for block in blocks:
            if block['block_number'] == self.blockNumber:
                return block['timestamp_utc']

    def allPairsFinder(self):
        df = pd.DataFrame(pairs)
        df['block_number'] = self.blockNumber
        timestamp = self.blockTimestampFinder()
        df['block_timestamp_utc'] = timestamp
        return df
    
    def latestPairSyncEventFinder(self, address):
        for event in sync_events:
            if event['block_number'] <= self.blockNumber and event['address'] == address:
                df = pd.DataFrame({'reserve0': [event['reserve0']], 'reserve1': [event['reserve1']]})
                return df
        return None  
    
    def pairSyncEventChecker(self):
        if self.pairs.empty:
            return None
        merged_list = []
        for address in self.pairs['contract_address']:
            try:
                df = self.latestPairSyncEventFinder(address)
                merged_list.append(df)
            except:
                print(f"No record for pair with address of {address}")
        df = pd.concat([self.pairs, *merged_list], axis=1)
        return df
    
    def pairMintEventFinder(self, address):
        results = []
        for event in mint_events:
            if event['block_number'] == self.blockNumber and event['address'] == address:
                df = pd.DataFrame(event, index=[0])
                results.append(df)
        if len(results) == 0:
            return None
        df_raw_mints = pd.concat(results, ignore_index=True)
        num_mints = len(df_raw_mints)
        mints_0 = Decimal(int(np.sum(df_raw_mints['amount0'].to_numpy())))
        mints_1 = Decimal(int(np.sum(df_raw_mints['amount1'].to_numpy())))
        data = [[num_mints, mints_0, mints_1]]
        cols = ['num_mints', 'mints_0', 'mints_1']
        df = pd.DataFrame(data, columns=cols)
        return df 
    
    def pairMintEventChecker(self):
        pairs = self.syncs
        merged_list = []
        for address in pairs['contract_address']:
            try:
                df_mints = self.pairMintEventFinder(address)
                merged_list.append(df_mints)
            except:
                print(f"No mint records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    def pairBurnEventFinder(self, address):
        results = []
        for event in burn_events:
            if event['block_number'] == self.blockNumber and event['address'] == address:
                df = pd.DataFrame(event, index=[0])
                results.append(df)
        if len(results) == 0:
            return None
        df_raw_burns = pd.concat(results, ignore_index=True)
        num_burns = len(df_raw_burns)
        burns_0 = Decimal(int(np.sum(df_raw_burns['amount0'].to_numpy())))
        burns_1 = Decimal(int(np.sum(df_raw_burns['amount1'].to_numpy())))
        data = [[num_burns, burns_0, burns_1]]
        cols = ['num_burns', 'burns_0', 'burns_1']
        df = pd.DataFrame(data, columns=cols)
        return df 
    
    def pairBurnEventChecker(self):
        pairs = self.mints
        merged_list = []
        for address in pairs['contract_address']:
            try:
                df_burns = self.pairBurnEventFinder(address)
                merged_list.append(df_burns)
            except:
                print(f"No burn records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    def pairSwapEventFinder(self, address):
        results = []
        for event in swap_events:
            if event['block_number'] == self.blockNumber and event['address'] == address:
                df = pd.DataFrame(event, index=[0])
                results.append(df)
        if len(results) == 0:
            return None
        df_raw_swaps = pd.concat(results, ignore_index=True)
        num_swaps_0 = df_raw_swaps[(df_raw_swaps['amount0_in'] > 0) | (df_raw_swaps['amount0_out'] > 0)]['amount0_in'].count()
        num_swaps_1 = df_raw_swaps[(df_raw_swaps['amount1_in'] > 0) | (df_raw_swaps['amount1_out'] > 0)]['amount1_in'].count()
        volume_0 = Decimal(int(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_in'] > 0, 'amount0_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount0_out'] > 0, 'amount0_out'].to_numpy()))))
        volume_1 = Decimal(int(np.abs(np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_in'] > 0, 'amount1_in'].to_numpy()) - np.sum(df_raw_swaps.loc[df_raw_swaps['amount1_out'] > 0, 'amount1_out'].to_numpy()))))
        data = [[num_swaps_0, num_swaps_1, volume_0, volume_1]]
        cols = ['num_swaps_0', 'num_swaps_1', 'volume_0', 'volume_1']
        df = pd.DataFrame(data, columns=cols)
        return df 
    
    def pairSwapEventChecker(self):
        pairs = self.burns
        merged_list = []
        for address in pairs['contract_address']:
            try:
                df_swaps = self.pairSwapEventFinder(address)
                merged_list.append(df_swaps)
            except:
                print(f"No swap records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    def latestTokenTotalSupplyFinder(self, address):
        for event in total_supply:
            if event['block_number'] <= self.blockNumber and event['address'] == address:
                df = pd.DataFrame({'total_supply': [event['total_supply']]})
                return df
        return None  
    
    def tokenTotalSupplyChecker(self):
        pairs = self.swaps
        merged_list = []
        for address in pairs['contract_address']:
            try:
                df_swaps = self.latestTokenTotalSupplyFinder(address)
                merged_list.append(df_swaps)
            except:
                print(f"No token total supply records for pair with address of {address}")
        df = pd.concat([pairs, *merged_list], axis=1)
        return df
    
    def summarizer(self):
        df = self.summary
        df.fillna(0, inplace=True)
        columns_to_check = ['total_supply', 'reserve0', 'reserve1', 'num_swaps_0', 'num_swaps_1', 'num_mints', 'num_burns', 'mints_0', 'mints_1', 'burns_0', 'burns_1', 'volume_0', 'volume_1']
        for col in columns_to_check:
            if col not in df.columns:
                df[col] = 0
        return df