from django.db import models

class SummaryType(models.Model):
    class Meta:
        ordering = ['summary_description']
        db_table = 'summary_type'

    summary_description = models.CharField(max_length=100, blank=True, null=True)
    data_frequency = models.CharField(max_length=3, blank=True, null=True)


