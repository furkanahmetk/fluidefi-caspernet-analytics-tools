from django.db import models


class BlockSummary(models.Model):
  class Meta:
    db_table = 'block_summary'
    unique_together = [["address", "block_number"]]

  id = models.AutoField(primary_key=True)
  address = models.CharField(max_length=100)
  block_timestamp_utc = models.DateTimeField()
  reserve0 = models.FloatField()
  reserve1 = models.FloatField()
  num_mints = models.BigIntegerField()
  mints_0 = models.FloatField()
  mints_1 = models.FloatField()
  num_swaps_0 = models.BigIntegerField()
  num_swaps_1 = models.BigIntegerField()
  num_mints = models.BigIntegerField()
  num_burns = models.BigIntegerField()
  burns_0 = models.FloatField()
  burns_1 = models.FloatField()
  volume_0 = models.FloatField()
  volume_1 = models.FloatField()
  block_number = models.IntegerField()
  total_supply = models.DecimalField(max_digits=155, decimal_places=0)