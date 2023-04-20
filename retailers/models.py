from django.db import models


# Create your models here.
class Retailers(models.Model):
    rank = models.IntegerField(null=True)
    name = models.CharField(null=False, max_length=256)
    country_of_origin = models.CharField(null=False, max_length=25)
    retail_revenue = models.FloatField(null=True)
    parent_company_revenue = models.FloatField(null=True)
    parent_company_net_income = models.FloatField(null=True)
    dominant_operational_format = models.CharField(null=True, max_length=256)
    countries_of_operation = models.IntegerField(null=True)
    retail_revenue_cagr = models.FloatField(null=True)

    def __str__(self):
        return self.name, self.dominant_operational_format