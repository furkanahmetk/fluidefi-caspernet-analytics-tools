from django.db import models

class LiquidityPool(models.Model):

    class Meta:
        managed = False
        db_table = 'liquidity_pool'
        unique_together = (('contract_address', 'network_id'), ('contract_address', 'network_id'),)

    def __unicode__(self):
        return self.id

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    fee_taken = models.FloatField(blank=True, null=True)
    fee_earned = models.FloatField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    contract_address = models.CharField(max_length=100)
    network_id = models.IntegerField(blank=True, null=True)
    platform_id = models.IntegerField(blank=True, null=True)
    created_at_block_number = models.IntegerField(blank=True, null=True)
    created_at_timestamp_utc = models.DateTimeField(blank=True, null=True)
    token0_symbol = models.CharField(max_length=12, blank=True, null=True)
    token1_symbol = models.CharField(max_length=12, blank=True, null=True)
    token0_address = models.CharField(max_length=100, blank=True, null=True)
    token1_address = models.CharField(max_length=100, blank=True, null=True)
    token0_collateral = models.IntegerField(blank=True, null=True)
    token1_collateral = models.IntegerField(blank=True, null=True)
    lp_token0_id = models.IntegerField(blank=True, null=True)
    lp_token1_id = models.IntegerField(blank=True, null=True)
    lp_watchlevel = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    last_processed = models.DateTimeField(blank=True, null=True)




