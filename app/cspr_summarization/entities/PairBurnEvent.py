from django.db import models

class PairBurnEvent(models.Model):
    class Meta:
        db_table = 'raw_pair_burn_event'
        unique_together = [["transaction_hash", "log_index"]]
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=100, db_column='address')
    block_number = models.IntegerField(db_column='block_number')
    block_hash = models.CharField(max_length=66, db_column='block_hash')
    log_index = models.IntegerField(db_column='log_index')
    sender = models.CharField(max_length=100, db_column='sender')
    amount0 = models.DecimalField(max_digits=155, decimal_places=0, db_column='amount0')
    amount1 = models.DecimalField(max_digits=155, decimal_places=0, db_column='amount1')
    receiver = models.CharField(max_length=100, db_column='receiver')
    transaction_hash = models.CharField(max_length=100, db_column='transaction_hash')
    transaction_index = models.IntegerField(db_column='transaction_index')

