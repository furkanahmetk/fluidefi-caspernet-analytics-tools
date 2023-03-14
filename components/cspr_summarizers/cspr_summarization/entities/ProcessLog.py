from django.db import models

class ProcessLog(models.Model):
    class Meta:
        db_table = 'process_log'
    id = models.AutoField(primary_key=True)
    process_name = models.CharField(max_length=100, unique=True)
    block_number = models.IntegerField()
    start_block_number = models.IntegerField()
    end_block_number = models.IntegerField()
    timestamp_utc = models.DateTimeField()
    deploy_hash = models.CharField(max_length=66)
    note = models.TextField()
    last_processed = models.DateTimeField()