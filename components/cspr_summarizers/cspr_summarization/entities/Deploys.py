from django.db import models

class Deploys(models.Model):
    class Meta:
        db_table = 'deploys'
    id = models.AutoField(primary_key=True)
    deploy_index = models.IntegerField()
    deploy_hash = models.CharField(max_length=64, unique=True)
    account = models.CharField(max_length=68)
    timestamp_utc = models.DateTimeField()
    ttl = models.CharField(max_length=64)
    gas_price = models.IntegerField()
    body_hash = models.CharField(max_length=64)
    dependencies = models.CharField(max_length=64, blank=True, null=True)
    chain_name = models.CharField(max_length=100)
    parsed_payment_amount = models.CharField(max_length=155)
    contract_hash = models.CharField(max_length=64)
    entry_point = models.CharField(max_length=200)
    block_hash = models.CharField(max_length=64)
    block_number = models.IntegerField()
    cost = models.CharField(max_length=155)
    payment = models.JSONField()
    execution_results = models.JSONField(null=True, blank=True)
