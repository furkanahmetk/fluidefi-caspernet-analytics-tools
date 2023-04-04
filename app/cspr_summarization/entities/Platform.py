from django.db import models
class Platform(models.Model):
    name = models.CharField(max_length=100)
    full_name = models.CharField(unique=True, max_length=100, blank=True, null=True)
    router_address = models.CharField(max_length=42, blank=True, null=True)
    factory_address = models.CharField(max_length=42, blank=True, null=True)
    network = models.IntegerField(blank=True, null=True)
    symbol = models.CharField(max_length=5, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    url_prefix = models.CharField(max_length=255, blank=True, null=True)
    platform_type = models.IntegerField()
    fl_supported = models.BooleanField(blank=True, null=True)
    platform_image_path = models.CharField(max_length=255, blank=True, null=True)
    token_url_prefix = models.CharField(max_length=255, blank=True, null=True)
    lp_url_prefix = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'platform'