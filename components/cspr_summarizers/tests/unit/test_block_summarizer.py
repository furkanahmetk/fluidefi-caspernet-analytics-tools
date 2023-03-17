import sys
sys.path.insert(0, "../")
from mocks.block_summarizer import MockBlockSummarizer
import unittest

blockSummarizer = MockBlockSummarizer(1393081)

class TestBlockSummarizer(unittest.TestCase):
    def test_blockTimestampFinder(self):
        result = blockSummarizer.blockTimestampFinder()
        self.assertEqual(result, '2023-01-09 09:55:39.648+00')

    def test_allPairsFinder(self):
        result = blockSummarizer.allPairsFinder()
        self.assertIsNotNone(result)  
    
    def test_latestPairSyncEventFinder(self):
        result = blockSummarizer.latestPairSyncEventFinder('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')  
        falsy_result = blockSummarizer.latestPairSyncEventFinder('cf56de334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')  
        self.assertIsNotNone(result)
        self.assertIsNone(falsy_result)
        
    def test_pairSyncEventChecker(self):
        result = blockSummarizer.pairSyncEventChecker()
        self.assertIsNotNone(result)
        
    def test_pairMintEventFinder(self):
        result = blockSummarizer.pairMintEventFinder('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNotNone(result)
        falsy_result = blockSummarizer.pairMintEventFinder('cf56e334d481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNone(falsy_result)
        
    def test_pairMintEventChecker(self):
        result = blockSummarizer.pairMintEventChecker()
        self.assertIsNotNone(result)
        
    def test_pairBurnEventFinder(self):
        result = blockSummarizer.pairBurnEventFinder('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNotNone(result)
        falsy_result = blockSummarizer.pairBurnEventFinder('cf56e334d481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNone(falsy_result)
        
    def test_pairBurnEventChecker(self):
        result = blockSummarizer.pairBurnEventChecker()
        self.assertIsNotNone(result)
        
    def test_pairSwapEventFinder(self):
        result = blockSummarizer.pairSwapEventFinder('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNotNone(result)
        falsy_result = blockSummarizer.pairSwapEventFinder('cf56e334481fe2dbf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')
        self.assertIsNone(falsy_result)
    
    def test_pairSwapEventChecker(self):
        result = blockSummarizer.pairSwapEventChecker()
        self.assertIsNotNone(result)
        
    def test_latestTokenTotalSupplyFinder(self):
        result = blockSummarizer.latestTokenTotalSupplyFinder('cf56e334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')  
        falsy_result = blockSummarizer.latestTokenTotalSupplyFinder('cf56de334481fe2bf0530e0c03a586d2672da8bfe1d1d259ea91457a3bd8971e0')  
        self.assertIsNotNone(result)
        self.assertIsNone(falsy_result)
        
    def test_tokenTotalSupplyChecker(self):
        result = blockSummarizer.tokenTotalSupplyChecker()
        self.assertIsNotNone(result)
        
    def test_summarizer(self):
        result = blockSummarizer.summarizer()
        self.assertIsNotNone(result)

    

if __name__ == '__main__':  
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBlockSummarizer)
    unittest.TextTestRunner(verbosity=2).run(suite)

    