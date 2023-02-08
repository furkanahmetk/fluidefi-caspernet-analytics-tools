from django.db import models

class Block(models.Model):
  class Meta:
    db_table = 'blocks'
  block_hash = models.CharField(max_length=64)
  parent_hash = models.CharField(max_length=64)
  state_root_hash = models.CharField(max_length=64)
  body_hash = models.CharField(max_length=64)
  random_bit = models.BooleanField()
  accumulated_seed = models.CharField(max_length=64)
  era_end = models.BooleanField()
  timestamp_utc = models.DateTimeField()
  era_id = models.IntegerField()
  block_number = models.AutoField(primary_key=True)
  protocol_version = models.CharField(max_length=20)
  proposer = models.CharField(max_length=68)
  deploy_hashes = models.TextField()
  transfer_hashes = models.TextField()
  api_version = models.CharField(max_length=20)
