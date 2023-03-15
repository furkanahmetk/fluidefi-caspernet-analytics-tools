import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()
from cspr_summarization.entities.BlockSummary import BlockSummary
from cspr_summarization.entities.BlockHours import BlockHours
import logging
import schedule
import time
logging.basicConfig(level=logging.INFO)

############################################################################
## START OF APPLICATION
############################################################################

from cspr_summarization.services.lp_block_summarizer.lp_block_summarizer import LPBlockSummarizer

def main():
    try:
        latest_block_hour = BlockHours.objects.using('default').values('block_number').latest('block_number')['block_number']
        try:
            latest_block_summary = BlockSummary.objects.using('default').values('block_number').latest('block_number')['block_number']
        except:
            latest_block_summary = BlockHours.objects.using('default').values('block_number').order_by('block_number').first()['block_number']
    except:
        logging.warning('The service could not be started! Please populate BlockHours data before running the service as no data was found on the BlockHours table')
        return

    
    if latest_block_hour >= latest_block_summary:
        for i in range(latest_block_summary, latest_block_hour + 1):
            try:
                lpBlockSummarizer = LPBlockSummarizer(i)
                lpBlockSummarizer.summarizer()
            except:
                logging.error(f'Failed to summarize for block {i}')

if __name__ == '__main__':
    schedule.every(1).minutes.do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)

        