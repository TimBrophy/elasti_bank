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
import os


def delete_log_file(filename):
    # Get the log directory within the project's base directory
    log_dir = os.path.join(settings.BASE_DIR, 'log_files')
    os.makedirs(log_dir, exist_ok=True)

    # Get the full path to the log file
    filepath = os.path.join(log_dir, filename)

    if os.path.exists(filepath):
        os.remove(filepath)


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
    if index_name == 'transactions':
        mapping = {
            "properties": {
                "location": {
                    "type": "geo_point"
                },
                "text_field": {
                  "type": "text"
                },
                # "description-vector": {
                #     "type": "dense_vector",
                #     "dims": 768,
                #     "index": 'true',
                #     "similarity": "l2_norm"
                # },
                "ml.tokens": {
                    "type": "rank_features"
                },
                "timestamp": {
                    "type": "date"
                }

            }
        }
        index_settings = {
            'default_pipeline': 'transactions-elser-v1',
            "number_of_replicas": 1

        }
    elif index_name == 'search_history':
        mapping = {
            'properties': {
                "timestamp": {
                    "type": "date"
                }
            }
        }
        index_settings = {
            "number_of_replicas": 1
        }
    else:
        mapping = {
            'properties': {
                'location': {
                    'type': 'geo_point'
                },
                "timestamp": {
                    "type": "date"
                }
            }
        }
        index_settings = {
            "number_of_replicas": 1
        }

    response = es.indices.create(index=index_name, body={'mappings': mapping, 'settings': index_settings})
    return response


class Command(BaseCommand):
    help = 'Export data to Elasticsearch'


    def handle(self, *args, **kwargs):

        es = Elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            http_auth=(settings.ES_USER, settings.ES_PASS)

        )


        delete_level = 'users'
        if delete_level == 'users':
            # response = input(
            #     "Do you want to delete all users and all data related to users? This effectively means you "
            #     "will wipe all records such as bank accounts, transactions and applications. (yes/no)")
            # if response.lower() == "yes":
            print("Deleting all user related data. Forever.")
            CustomUser.objects.exclude(username__in=['demo_user', 'timb']).delete()
            BankAccount.objects.all().delete()
            BankAccountApplications.objects.all().delete()
            DebittTransactionExportLog.objects.all().delete()
            CreditTransactionExportLog.objects.all().delete()
            Activity.objects.all().delete()

            delete_index('transactions')
            create_index('transactions')
            delete_index('bank-accounts')
            create_index('bank-accounts')
            delete_index('account-applications')
            create_index('account-applications')
            delete_index('interactions')
            create_index('interactions')
            delete_index('search_history')
            create_index('search_history')

            delete_log_file('transactions.log')
            delete_log_file('bank_account_data.log')
            delete_log_file('application_data.log')
            delete_log_file('activity_data.log')

            # elif response.lower() == "no":
            #     print("Operation aborted.")
            # else:
            #     print("Invalid input.")

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

                delete_log_file('transactions.log')
                delete_log_file('bank-accounts.log')

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
                delete_log_file('transactions.log')

            elif response.lower() == "no":
                print("Operation aborted.")
            else:
                print("Invalid input.")
        else:
            print("You have not provided a valid operation. Please try again.")
