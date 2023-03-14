from django.db import models
from cspr_summarization.entities import UniswapV2Pair

class LpSummary(models.Model):
    class Meta:
        db_table = 'lp_summary3_latest'
        unique_together = [["liquidity_pool", "summary_type", "close_timestamp_utc"]]

    liquidity_pool = models.ForeignKey(UniswapV2Pair, models.DO_NOTHING)
    summary_type = models.ForeignKey('SummaryType', models.DO_NOTHING, db_column='summary_type')
    open_timestamp_utc = models.DateTimeField()
    close_timestamp_utc = models.DateTimeField()
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
    open_reserve_0 = models.FloatField(blank=True, null=True)
    open_reserve_1 = models.FloatField(blank=True, null=True)
    close_reserve_0 = models.FloatField(blank=True, null=True)
    close_reserve_1 = models.FloatField(blank=True, null=True)
