from django.db import models

class TokenTotalSupply(models.Model):
    class Meta:
        db_table = 'token_total_supply'
        unique_together = [["block_number", "token_address"]]
    token_address = models.CharField(max_length=100)
    block_number = models.IntegerField()
    total_supply = models.DecimalField(max_digits=155, decimal_places=0)