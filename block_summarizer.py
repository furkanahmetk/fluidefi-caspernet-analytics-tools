import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()
from cspr_summarization.entities.BlockSummary import BlockSummary
from cspr_summarization.entities.BlockHours import BlockHours
############################################################################
## START OF APPLICATION
############################################################################

from cspr_summarization.services.lp_block_summarizer.lp_block_summarizer import LPBlockSummarizer

def main():
    latest_block_summary = BlockSummary.objects.using('default').values('block_number').latest('block_number')['block_number']
    latest_block_hour = BlockHours.objects.using('default').values('block_number').latest('block_number')['block_number']
    
    if latest_block_hour >= latest_block_summary:
        for i in range(latest_block_summary, latest_block_hour + 1):
            lpBlockSummarizer = LPBlockSummarizer(i)
            lpBlockSummarizer.summarizer()

if __name__ == '__main__':
    main()
    