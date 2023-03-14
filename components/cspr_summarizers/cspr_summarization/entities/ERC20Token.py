from django.db import models

class ERC20Token(models.Model):
    class Meta:
        db_table = 'erc20_token'
    id = models.AutoField(primary_key=True)
    token_address = models.CharField(max_length=100, unique=True)
    token_decimals = models.IntegerField()
    token_name = models.CharField(max_length=100)
    token_symbol = models.CharField(max_length=100)
    is_lp_token = models.BooleanField()
    token_type = models.CharField(max_length=20)
    passed_qa = models.BooleanField()