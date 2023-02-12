from django.db import models

class BlockHours(models.Model):
    class Meta:
        db_table = 'block_hours'
        unique_together = [["block_number", "hourly_timestamp_utc"]]
    id = models.AutoField(primary_key=True)
    block_number = models.IntegerField(unique=True)
    block_timestamp_utc = models.DateTimeField()
    hourly_timestamp_utc = models.DateTimeField(unique=True)
