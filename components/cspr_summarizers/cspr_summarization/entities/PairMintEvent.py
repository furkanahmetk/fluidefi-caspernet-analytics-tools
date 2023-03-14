from django.db import models

class PairMintEvent(models.Model):
    class Meta:
        db_table = 'raw_pair_mint_event'
        unique_together = [["transaction_hash", "log_index"]]
    address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=66)
    log_index = models.IntegerField()
    sender = models.CharField(max_length=100)
    amount0 = models.DecimalField(max_digits=155, decimal_places=0)
    amount1 = models.DecimalField(max_digits=155, decimal_places=0)
    pair = models.CharField(max_length=100, null=True)
    transaction_hash = models.CharField(max_length=100)
    transaction_index = models.IntegerField()