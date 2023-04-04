from django.db import models
from django.contrib.auth.models import User

class UserFilters(models.Model):
    # Even though the table is AuthUser in the schema, use model User for Django
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    use_filters = models.BooleanField(blank=True, null=True)
    filter_version = models.IntegerField(blank=True, null=True)
    collateral_fiat = models.BooleanField()
    collateral_crypto = models.BooleanField()
    collateral_algorithmic = models.BooleanField()
    collateral_metals = models.BooleanField()
    collateral_other = models.BooleanField()
    poolsize_min = models.IntegerField()
    poolsize_max = models.BigIntegerField(blank=True, null=True)
    volume_min = models.IntegerField()
    volume_max = models.BigIntegerField(blank=True, null=True)
    ill_min = models.FloatField(blank=True, null=True)
    ill_max = models.FloatField(blank=True, null=True)
    yff_min = models.FloatField(blank=True, null=True)
    transactions_min_day = models.IntegerField()
    transactions_min_week = models.IntegerField()
    pool_size_t1d_min = models.IntegerField(blank=True, null=True)
    pool_size_t1d_max = models.IntegerField(blank=True, null=True)
    pool_size_t7d_min = models.IntegerField(blank=True, null=True)
    pool_size_t7d_max = models.IntegerField(blank=True, null=True)
    volume_t1d_min = models.IntegerField(blank=True, null=True)
    volume_t1d_max = models.IntegerField(blank=True, null=True)
    volume_t7d_min = models.IntegerField(blank=True, null=True)
    volume_t7d_max = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_filters'