import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

############################################################################
## START OF APPLICATION
############################################################################

from cspr_summarization.services.lp_block_summarizer import LPBlockSummarizer

def main():
    # Setting block number to a recent block
    block_number = 1393081
    
    # Instantiating LPBlockSummarizer
    lpBlockSummarizer = LPBlockSummarizer(block_number)
    
    # Generating summary dataframes
    df = lpBlockSummarizer.summarizer()
    
    # Outputting summary
    return df
    
if __name__ == '__main__':
    main()
    