from django.db import models

class ERC20ApprovalEvent(models.Model):
    class Meta:
        db_table = 'erc20_approval_event'
        unique_together = [["transaction_hash", "log_index"]]
    address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=66)
    log_index = models.IntegerField()
    owner = models.CharField(max_length=100)
    spender = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=155, decimal_places=0)
    transaction_hash = models.CharField(max_length=100)
    transaction_index = models.IntegerField()
