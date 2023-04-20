import time

from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountType, BankAccountApplications
from transactions.models import CreditTransactions, DebitTransactions, CreditTransactionType, DebitTransactionType
from export.models import DebittTransactionExportLog, CreditTransactionExportLog
from activity.models import Activity
from elasticsearch import Elasticsearch, exceptions
from elastic_enterprise_search import EnterpriseSearch, AppSearch


def delete_index(index_name):
    es = Elasticsearch(
        cloud_id=settings.ES_CLOUD_ID,
        http_auth=(settings.ES_USER, settings.ES_PASS)

    )
    if not es.indices.exists(index=index_name):
        print(f"Index '{index_name}' does not exist!")
    else:
        es_response = es.indices.delete(index=index_name)
    return


def create_index(index_name):
    es = Elasticsearch(
        cloud_id=settings.ES_CLOUD_ID,
        http_auth=(settings.ES_USER, settings.ES_PASS)

    )

    mapping = {
        'properties': {
            'location': {
                'type': 'geo_point'
            }
        }
    }

    response = es.indices.create(index=index_name, body={'mappings': mapping})
    return response


class Command(BaseCommand):
    help = 'Export data to Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument('delete-level', type=str,
                            help='Indicates the level as which you want to clear data')

    def handle(self, *args, **kwargs):

        es = Elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            http_auth=(settings.ES_USER, settings.ES_PASS)

        )

        app_search = AppSearch("https://fsi-use-cases.ent.eu-central-1.aws.cloud.es.io",
                               http_auth="private-45sw3rhm73up2nqrg1np7xwm")

        delete_level = kwargs['delete-level']
        if delete_level == 'users':
            response = input(
                "Do you want to delete all users and all data related to users? This effectively means you "
                "will wipe all records such as bank accounts, transactions and applications. (yes/no)")
            if response.lower() == "yes":
                print("Deleting all user related data. Forever.")
                CustomUser.objects.exclude(username__in=['jake', 'timb']).delete()
                BankAccount.objects.all().delete()
                BankAccountApplications.objects.all().delete()
                DebittTransactionExportLog.objects.all().delete()
                CreditTransactionExportLog.objects.all().delete()
                Activity.objects.all().delete()

                app_search.delete_engine(engine_name="search-transactions")
                time.sleep(60)
                app_search.create_engine(engine_name="search-transactions", language="en")

                delete_index('transactions')
                create_index('transactions')
                delete_index('bank-accounts')
                create_index('bank-accounts')
                delete_index('account-applications')
                create_index('account-applications')
                delete_index('interactions')
                create_index('interactions')

            elif response.lower() == "no":
                print("Operation aborted.")
            else:
                print("Invalid input.")

        elif delete_level == 'bank-accounts':
            response = input(
                "Do you want to delete all bank accounts and all data related to those accounts? This means you "
                "will remove all bank accounts and transactions. (yes/no)")
            if response.lower() == "yes":
                print("Deleting all bank account data. Forever.")
                BankAccount.objects.all().delete()
                BankAccountApplications.objects.all().delete()
                DebittTransactionExportLog.objects.all().delete()
                CreditTransactionExportLog.objects.all().delete()
                delete_index('transactions')
                create_index('transactions')
                delete_index('bank-accounts')
                create_index('bank-accounts')

            elif response.lower() == "no":
                print("Operation aborted.")
            else:
                print("Invalid input.")

        elif delete_level == 'transactions':
            response = input("Do you want to delete all transactions, including the export log? This means you "
                             "will remove all transactions and need to repopulate them. (yes/no)")
            if response.lower() == "yes":
                print("Deleting all transaction data. Forever.")
                CreditTransactions.objects.all().delete()
                DebitTransactions.objects.all().delete()
                DebittTransactionExportLog.objects.all().delete()
                CreditTransactionExportLog.objects.all().delete()
                delete_index('transactions')
                create_index('transactions')
            elif response.lower() == "no":
                print("Operation aborted.")
            else:
                print("Invalid input.")
        else:
            print("You have not provided a valid operation. Please try again.")
