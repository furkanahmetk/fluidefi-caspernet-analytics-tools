from django.db import models

class NativePriceUSD(models.Model):
    class Meta:
        db_table = 'native_price_usd'
    block_number = models.IntegerField(primary_key=True, db_column='block_number')
    cspr_price_usd = models.DecimalField(max_digits=24, decimal_places=16, db_column='cspr_price_usd')
    timestamp_utc = models.DateTimeField(db_column='timestamp_utc')
