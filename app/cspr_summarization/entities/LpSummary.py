from django.db import models
from cspr_summarization.entities.LiquidityPool import LiquidityPool
from cspr_summarization.entities.SummaryType import SummaryType


class LpSummary(models.Model):
    liquidity_pool = models.ForeignKey(LiquidityPool, models.DO_NOTHING, blank=True, null=True)
    summary_type = models.ForeignKey('SummaryType', models.DO_NOTHING, db_column='summary_type', blank=True, null=True)
    open_timestamp_utc = models.DateTimeField(blank=True, null=True)
    close_timestamp_utc = models.DateTimeField(blank=True, null=True)
    total_period_return = models.FloatField(blank=True, null=True)
    yield_on_lp_fees = models.FloatField(blank=True, null=True)
    price_change_ret = models.FloatField(blank=True, null=True)
    hodl_return = models.FloatField(blank=True, null=True)
    fees_apy = models.FloatField(blank=True, null=True)
    total_apy = models.FloatField(blank=True, null=True)
    impermanent_loss_level = models.FloatField(blank=True, null=True)
    impermanent_loss_impact = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    transactions_period = models.IntegerField(blank=True, null=True)
    poolsize = models.FloatField(blank=True, null=True)
    open_poolsize = models.FloatField(blank=True, null=True)
    close_poolsize = models.FloatField(blank=True, null=True)
    open_reserve_0 = models.FloatField(blank=True, null=True)
    open_reserve_1 = models.FloatField(blank=True, null=True)
    close_reserve_0 = models.FloatField(blank=True, null=True)
    close_reserve_1 = models.FloatField(blank=True, null=True)
    open_price_0 = models.FloatField(blank=True, null=True)
    open_price_1 = models.FloatField(blank=True, null=True)
    high_price_0 = models.FloatField(blank=True, null=True)
    high_price_1 = models.FloatField(blank=True, null=True)
    low_price_0 = models.FloatField(blank=True, null=True)
    low_price_1 = models.FloatField(blank=True, null=True)
    close_price_0 = models.FloatField(blank=True, null=True)
    close_price_1 = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lp_summary'
        unique_together = (('liquidity_pool', 'summary_type', 'close_timestamp_utc'),)
        ordering = ['-close_timestamp_utc', 'liquidity_pool']

