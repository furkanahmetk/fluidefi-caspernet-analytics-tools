import sys
sys.dont_write_bytecode = True

# Django specific settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from cspr_summarization.entities.block import *
import pandas as pd

############################################################################
## START OF APPLICATION
############################################################################

# Get data from the database using the Django ORM
block_table = Block.objects.values()

# Convert the data to a pandas DataFrame
df_blocks = pd.DataFrame.from_records(block_table)
print(df_blocks)