from django.db import models
from cspr_summarization.entities.ModelType import ModelType
from cspr_summarization.entities.Currency import Currency
from django.contrib.auth.models import User
class UserLpList(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    lp_list_name = models.CharField(max_length=100, blank=True, null=True)
    timestamp_utc = models.DateTimeField(blank=True, null=True)
    model_type = models.ForeignKey(ModelType, models.DO_NOTHING, blank=True, null=True)
    investment_size = models.FloatField(blank=True, null=True)
    investment_timestamp_utc = models.DateTimeField(blank=True, null=True)
    investment_end_timestamp_utc = models.DateTimeField(blank=True, null=True)
    currency = models.ForeignKey(Currency, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_lp_list'
