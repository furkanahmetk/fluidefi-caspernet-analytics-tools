from django.db import models

class ERC20TransferEvent(models.Model):
    class Meta:
        db_table = 'erc20_transfer_event'
        unique_together = [["transaction_hash", "log_index"]]
    id = models.AutoField(primary_key=True)
    address = models.CharField(max_length=100, db_column='address')
    block_number = models.IntegerField(db_column='block_number')
    block_hash = models.CharField(max_length=66, db_column='block_hash')
    log_index = models.IntegerField(db_column='log_index')
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=155, decimal_places=0)
    transaction_hash = models.CharField(max_length=100, db_column='transaction_hash')
    transaction_index = models.IntegerField(db_column='transaction_index')