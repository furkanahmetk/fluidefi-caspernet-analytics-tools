from django.db import models

class ModelType(models.Model):
    model_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'model_type'