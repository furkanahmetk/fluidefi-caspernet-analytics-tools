from django.db import models

class UniswapV2Pair(models.Model):
    class Meta:
        db_table = 'all_pairs'
        unique_together = [["factoryAddress", "pairCreationIndex"]]
    contract_address = models.CharField(max_length=100, unique=True)
    factory_address = models.CharField(max_length=100)
    pair_creation_index = models.IntegerField()
    added_datetime_utc = models.DateTimeField()
    added_to_platform = models.BooleanField()
    token0_decimals = models.IntegerField()
    token1_decimals = models.IntegerField()
    token0_address = models.CharField(max_length=100)
    token1_address = models.CharField(max_length=100)
    first_mint_event_block_number = models.IntegerField(null=True)
    first_mint_event_timestamp_utc = models.DateTimeField(null=True)

    
