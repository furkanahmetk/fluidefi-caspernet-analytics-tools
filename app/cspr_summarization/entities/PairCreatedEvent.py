from django.db import models

class PairCreatedEvent(models.Model):
    class Meta:
        db_table = 'pair_created_event'
        unique_together = [["transaction_hash", "log_index"]]
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=66)
    log_index = models.IntegerField()
    token0 = models.CharField(max_length=100)
    token1 = models.CharField(max_length=100)
    pair = models.CharField(max_length=100)
    all_pairs_length = models.IntegerField(null=True)
    transaction_hash = models.CharField(max_length=100)
    transaction_index = models.CharField(max_length=100)