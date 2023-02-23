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

from cspr_summarization.services.lp_block_summarizer import LPBlockSummarizer

class TestBlockSummarizer(unittest.TestCase):
  def test_sync_summarizer(self):
    block_number=1393081

    lpBlockSummarizer = LPBlockSummarizer(block_number)
    sync_result = lpBlockSummarizer.pairSyncEventChecker()

    self.assertIsNotNone(sync_result)

  def test_mint_summarizer(self):
    block_number=1393081

    lpBlockSummarizer = LPBlockSummarizer(block_number)
    mint_result = lpBlockSummarizer.pairMintEventChecker()

    self.assertIsNotNone(mint_result)
  
  def test_burn_summarizer(self):
    block_number=1393081

    lpBlockSummarizer = LPBlockSummarizer(block_number)
    burn_result = lpBlockSummarizer.pairBurnEventChecker()

    self.assertIsNotNone(burn_result)
  
  def test_swap_summarizer(self):
    block_number=1393081

    lpBlockSummarizer = LPBlockSummarizer(block_number)
    swap_result = lpBlockSummarizer.pairSwapEventChecker()

    self.assertIsNotNone(swap_result)

if __name__ == '__main__':  
  unittest.main()

    