from django.db import models

class HourlyData(models.Model):
  class Meta:
    db_table = 'hourly_data'
    unique_together = ('address', 'open_timestamp_utc', 'close_timestamp_utc')
  
  id = models.AutoField(primary_key=True)
  address = models.CharField(max_length=100)
  open_timestamp_utc = models.DateTimeField()
  close_timestamp_utc = models.DateTimeField()
  close_reserves_0 = models.FloatField()
  close_reserves_1 = models.FloatField()
  num_swaps_0 = models.BigIntegerField()
  num_swaps_1 = models.BigIntegerField()
  num_mints = models.BigIntegerField()
  num_burns = models.BigIntegerField()
  mints_0 = models.FloatField()
  mints_1 = models.FloatField()
  burns_0 = models.FloatField()
  burns_1 = models.FloatField()
  volume_0 = models.FloatField()
  volume_1 = models.FloatField()
  max_block = models.IntegerField()
  close_lp_token_supply = models.DecimalField(max_digits=155, decimal_places=0)

  def __init__(self, address, open_timestamp_utc, close_timestamp_utc, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.address = address
    self.open_timestamp_utc = open_timestamp_utc
    self.close_timestamp_utc = close_timestamp_utc
    self.close_reserves_0 = 0
    self.close_reserves_1 = 0
    self.num_swaps_0 = 0
    self.num_swaps_1 = 0
    self.num_mints = 0
    self.num_burns = 0
    self.mints_0 = 0
    self.mints_1 = 0
    self.burns_0 = 0
    self.burns_1 = 0
    self.volume_0 = 0
    self.volume_1 = 0
    self.max_block = 0
    self.close_lp_token_supply = 0