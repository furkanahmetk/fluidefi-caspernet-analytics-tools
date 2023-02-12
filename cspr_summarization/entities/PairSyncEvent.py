from django.db import models

class PairSyncEvent(models.Model):
    class Meta:
        db_table = 'raw_pair_sync_event'
        unique_together = [["transaction_hash", "log_index"]]
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=66)
    log_index = models.IntegerField()
    reserve0 = models.DecimalField(max_digits=155, decimal_places=0)
    reserve1 = models.DecimalField(max_digits=155, decimal_places=0)
    transaction_hash = models.CharField(max_length=100)
    transaction_index = models.IntegerField()
