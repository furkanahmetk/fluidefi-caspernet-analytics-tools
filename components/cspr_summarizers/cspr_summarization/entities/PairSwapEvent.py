from django.db import models

class PairSwapEvent(models.Model):
    class Meta:
        db_table = 'raw_pair_swap_event'
        unique_together = [["transaction_hash", "log_index"]]
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=66)
    log_index = models.IntegerField()
    sender = models.CharField(max_length=100)
    amount0_in = models.DecimalField(max_digits=155, decimal_places=0)
    amount0_out = models.DecimalField(max_digits=155, decimal_places=0)
    amount1_in = models.DecimalField(max_digits=155, decimal_places=0)
    amount1_out = models.DecimalField(max_digits=155, decimal_places=0)
    receiver = models.CharField(max_length=100)
    transaction_hash = models.CharField(max_length=100)
    transaction_index = models.IntegerField()