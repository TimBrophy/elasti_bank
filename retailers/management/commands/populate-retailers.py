import csv
from django.core.management.base import BaseCommand
from retailers.models import Retailers


class Command(BaseCommand):
    help = 'Generate random bank transactions'

    def handle(self, *args, **kwargs):
        with open("/Users/timb/Dev/django_apm-master/data/cos2019.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                if row['parent_company_revenue'] == '':
                    parent_company_revenue = 0
                else:
                    parent_company_revenue = row['parent_company_revenue']

                if row['parent_company_net_income'] == '':
                    parent_company_net_income = 0
                else:
                    parent_company_net_income = row['parent_company_net_income']

                if row['retail_revenue_cagr'] == '':
                    retail_revenue_cagr = 0
                else:
                    retail_revenue_cagr = row['retail_revenue_cagr']

                instance = Retailers(
                    rank=row['rank'],
                    name=row['name'],
                    country_of_origin=row['country_of_origin'],
                    retail_revenue=float(row['retail_revenue']),
                    parent_company_revenue=parent_company_revenue,
                    parent_company_net_income=parent_company_net_income,
                    dominant_operational_format=row['dominant_operational_format'],
                    countries_of_operation=row['countries_of_operation'],
                    retail_revenue_cagr=retail_revenue_cagr
                )
                instance.save()
