from django.db import models

class Prefix(models.Model):
    class Meta:
        db_table = 'prefix'
    prefix_key = models.IntegerField(unique=True)
    prefix = models.CharField(max_length=30, unique=True)
    prefix_length = models.IntegerField()
