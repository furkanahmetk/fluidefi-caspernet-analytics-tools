from django.db import models
class Currency(models.Model):
    code = models.CharField(unique=True, max_length=3, blank=True, null=True)
    symbol = models.CharField(max_length=5, blank=True, null=True)
    network_id = models.IntegerField(blank=True, null=True)
    token_address = models.CharField(max_length=100, blank=True, null=True)
    display_name = models.CharField(max_length=15, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    html = models.CharField(max_length=30, blank=True, null=True)
    format = models.CharField(max_length=10, blank=True, null=True)
    active_fiat = models.BooleanField(blank=True, null=True)
    decimals = models.IntegerField(blank=True, null=True)
    token_type = models.IntegerField(blank=True, null=True)
    collateral_currency_backed_by = models.ForeignKey('self', models.DO_NOTHING, db_column='collateral_currency_backed_by', blank=True, null=True)
    collateral_currency_pegged_to = models.IntegerField(blank=True, null=True)
    last_updated_utc = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'currency'
        unique_together = (('token_address', 'network_id'),)
