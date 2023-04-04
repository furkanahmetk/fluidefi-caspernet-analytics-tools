from django.db import models
from cspr_summarization.entities.LiquidityPool import LiquidityPool
from cspr_summarization.entities.Currency import Currency

class LpList(models.Model):
    lp_list = models.ForeignKey('UserLpList', models.DO_NOTHING, blank=True, null=True)
    liquidity_pool = models.ForeignKey(LiquidityPool, models.DO_NOTHING, blank=True, null=True)
    contract_address = models.CharField(max_length=42, blank=True, null=True)
    lp_amount = models.DecimalField(max_digits=64, decimal_places=0, blank=True, null=True)
    currency = models.ForeignKey(Currency, models.DO_NOTHING, blank=True, null=True)
    token_address = models.CharField(max_length=100, blank=True, null=True)
    token_amount = models.DecimalField(max_digits=64, decimal_places=0, blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    lp_balance_eth = models.DecimalField(max_digits=64, decimal_places=0, blank=True, null=True)
    lp_list_percentage = models.FloatField(blank=True, null=True)
    lp_token_amount = models.DecimalField(max_digits=64, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lp_list'
