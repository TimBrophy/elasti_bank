import requests
from urllib.parse import urlencode
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountApplications
from transactions.models import CreditTransactions, DebitTransactions
from retailers.models import Retailers
from activity.models import Activity
from export.models import DebittTransactionExportLog, CreditTransactionExportLog
from elasticsearch import Elasticsearch, helpers
from elastic_enterprise_search import EnterpriseSearch, AppSearch
import uuid
import datetime
import re
import pandas as pd
from geopy.geocoders import Nominatim
import warnings
from django.conf import settings



warnings.filterwarnings("ignore", category=FutureWarning)

def actions_gen(data, index):
    for doc in data:
        action = {
            '_index': index,
            '_source': doc
        }
        yield action


def geocode_address(address):
    default_lat = 44.96
    default_lon = 103.77

    url_params = {
        'address': urlencode(address),
        'key': settings.GOOGLE_MAPS_API_KEY,
    }

    url = 'https://maps.googleapis.com/maps/api/geocode/json?' + urlencode(url_params)
    response = requests.get(url)

    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'OK':
            application_location = result['results'][0]['geometry']['location']
        else:
            application_location = (default_lat, default_lon)  # default location
    else:
        application_location = (default_lat, default_lon)  # default location

    return application_location


class Command(BaseCommand):
    help = 'Export data to Elasticsearch'

    def handle(self, *args, **kwargs):
        es = Elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            http_auth=(settings.ES_USER, settings.ES_PASS)

        )
        app_search = AppSearch(settings.APPSEARCH_ENDPOINT,
                               http_auth=settings.APPSEARCH_AUTH)

        exported_credit_transactions = CreditTransactionExportLog.objects.all().values('id')
        exported_debit_transactions = CreditTransactionExportLog.objects.all().values('id')
        ct_exported_log = list(exported_credit_transactions.values_list('id', flat=True))
        dt_exported_log = list(exported_debit_transactions.values_list('id', flat=True))

        users = CustomUser.objects.all()

        # loop through all users

        for u in users:
            # import the users' activities/interactions
            activities = Activity.objects.filter(user=u.id)
            if activities.count() > 0:
                activities_df = pd.DataFrame()
                for activity in activities:
                    target_string = str(activity.location)
                    # Regular expression to extract the latitude and longitude values
                    pattern = r"'longitude'\s*:\s*([-+]?\d*\.\d+|\d+).*'latitude'\s*:\s*([-+]?\d*\.\d+|\d+)"
                    # Find the latitude and longitude values in the input string
                    match = re.search(pattern, target_string)
                    if match:
                        # Create a dictionary to store the latitude and longitude values
                        location = {
                            "longitude": match.group(1),
                            "latitude": match.group(2)
                        }
                        activity_location = location
                    else:
                        activity_location = {
                            "longitude": 00.0000,
                            "latitude": 00.0000
                        }
                    record_id = uuid.uuid4()
                    activity_record = {
                        'id': record_id,
                        'User id': u.id,
                        'Username': u.username,
                        'Full name': u.first_name + ' ' + u.last_name,
                        'created_at': activity.created_at,
                        'Log message': activity.activity_log_message,
                        'location': {
                            'lat': activity_location['latitude'],
                            'lon': activity_location['longitude']
                        },
                        'Activity type': activity.activitytype.name
                    }
                    activities_df = activities_df.append(activity_record, ignore_index=True)
                activity_data = activities_df.to_dict(orient='records')
                helpers.bulk(es, actions_gen(activity_data, 'interactions'))

            # loop through all bank accounts for these users
            bankaccounts = BankAccount.objects.filter(user=u.id)
            if bankaccounts.count() > 0:
                # import the bank accounts
                bankaccounts_df = pd.DataFrame()
                for bankaccount in bankaccounts:
                    record_id = uuid.uuid4()
                    bankaccount_record = {
                        'id': record_id,
                        'User id': u.id,
                        'Username': u.username,
                        'Full name': u.first_name + ' ' + u.last_name,
                        'timestamp': datetime.datetime.now(),
                        'created_at': bankaccount.created_at,
                        'Bank Account Type': bankaccount.bankaccounttype.typename,
                        'Account number': bankaccount.account_number,
                        'Balance': bankaccount.balance
                    }
                    bankaccounts_df = bankaccounts_df.append(bankaccount_record, ignore_index=True)
                    bank_account_data = bankaccounts_df.to_dict(orient='records')
                    helpers.bulk(es, actions_gen(bank_account_data, 'bank-accounts'))

                    # get all the credit transactions and loop through
                    credittransactions = CreditTransactions.objects.filter(destination_account=bankaccount.id).exclude(
                        id__in=ct_exported_log)

                    credittransactions_df = pd.DataFrame()
                    records = []
                    for ct in credittransactions:
                        record_id = uuid.uuid4()
                        new_row = {
                            'id': record_id,
                            'timestamp': ct.created_at,
                            'User id': u.id,
                            'Username': u.username,
                            'Bank account': bankaccount.account_number,
                            'Account created date': bankaccount.created_at,
                            'Full name': u.first_name + ' ' + u.last_name,
                            'Source entity': ct.source_bank,
                            'Source account': ct.source_account,
                            'Sender': ct.from_name,
                            'Value': ct.value,
                            'Description': ct.description,
                            'Reference': ct.reference,
                            'Type': 'Credit',
                            'Sub-type': ct.transaction_type.name
                        }
                        if u.username == 'JK':
                            appsearch_url = "http://127.0.0.1:8000/my-transactions/transaction-detail/{}/{}".format(ct.id, ct.value)
                            new_row_appsearch = {
                                'id': record_id,
                                'timestamp': ct.created_at,
                                'user_id': u.id,
                                'username': u.username,
                                'bank_account': bankaccount.account_number,
                                'account_created_date': bankaccount.created_at,
                                'fullname': u.first_name + ' ' + u.last_name,
                                'source_entity': ct.source_bank,
                                'source_account': ct.source_account,
                                'sender': ct.from_name,
                                'value': ct.value,
                                'description': ct.description,
                                'reference': ct.reference,
                                'type': 'Credit',
                                'sub_type': ct.transaction_type.name,
                                'url': appsearch_url
                            }
                            records.append(new_row_appsearch)

                        credittransactions_df = credittransactions_df.append(new_row, ignore_index=True)
                        log_entry = CreditTransactionExportLog(id=ct.id,
                                                               exported_at=datetime.datetime.now(datetime.timezone.utc))
                        log_entry.save()
                    data = credittransactions_df.to_dict(orient='records')
                    helpers.bulk(es, actions_gen(data, 'transactions'))
                    if len(records):
                        response = app_search.index_documents(engine_name='search-transactions', documents=records)
                        print(response)
                    num_rows = credittransactions_df.shape[0]

                    # get all the debit transactions and loop through
                    debittransactions = DebitTransactions.objects.filter(
                        source_account=bankaccount.id).exclude(
                        id__in=dt_exported_log)

                    debittransactions_df = pd.DataFrame()
                    for dt in debittransactions:
                        records = []
                        retailers = Retailers.objects.filter(name=dt.recipient_name)
                        if retailers.exists():
                            category = retailers.first().dominant_operational_format
                        else:
                            category = 'Unspecified'

                        if dt.transaction_type.name == "Purchase":
                            # Regular expression to extract the latitude and longitude values
                            pattern = r"'longitude'\s*:\s*([-+]?\d*\.\d+|\d+).*'latitude'\s*:\s*([-+]?\d*\.\d+|\d+)"
                            # Find the latitude and longitude values in the input string
                            match = re.search(pattern, dt.description)
                            # Create a dictionary to store the latitude and longitude values
                            location = {
                                "longitude": match.group(1),
                                "latitude": match.group(2)
                            }
                            transaction_location = location
                        else:
                            transaction_location = {
                                "latitude": 00.000000,
                                "longitude": 00.000000
                            }

                        record_id = uuid.uuid4()
                        new_row = {
                            'id': record_id,
                            'timestamp': dt.created_at,
                            'User id': u.id,
                            'Username': u.username,
                            'Bank account': bankaccount.account_number,
                            'Account created date': bankaccount.created_at,
                            'Full name': u.first_name + ' ' + u.last_name,
                            'Destination entity': dt.destination_bank,
                            'Destination account': dt.destination_account,
                            'Recipient': dt.recipient_name,
                            'Value': dt.value,
                            'Description': dt.description,
                            'Reference': dt.reference,
                            'Type': 'Debit',
                            'Sub-type': dt.transaction_type.name,
                            'Category': category,
                            'location': {
                                "lat": transaction_location["latitude"],
                                "lon": transaction_location["longitude"]
                            }
                        }
                        if u.username == 'jake':
                            appsearch_url = "http://127.0.0.1:8000/my-transactions/transaction-detail/{}/-{}".format(dt.id, dt.value)
                            new_row_appsearch = {
                                'id': record_id,
                                'timestamp': dt.created_at,
                                'user_id': u.id,
                                'username': u.username,
                                'bank_account': bankaccount.account_number,
                                'account_created_date': bankaccount.created_at,
                                'fullname': u.first_name + ' ' + u.last_name,
                                'destination_entity': dt.destination_bank,
                                'destination_account': dt.destination_account,
                                'recipient': dt.recipient_name,
                                'value': dt.value,
                                'description': dt.description,
                                'reference': dt.reference,
                                'type': 'Debit',
                                'sub_type': dt.transaction_type.name,
                                'category': category,
                                'location': {
                                    "lat": transaction_location["latitude"],
                                    "lon": transaction_location["longitude"]
                                },
                                'url': appsearch_url
                            }
                            records.append(new_row_appsearch)
                        if len(records):
                            response = app_search.index_documents(engine_name='search-transactions', documents=records)
                            print(response)
                        debittransactions_df = debittransactions_df.append(new_row, ignore_index=True)
                        log_entry = DebittTransactionExportLog(id=dt.id,
                                                               exported_at=datetime.datetime.now(datetime.timezone.utc))
                        log_entry.save()

                    data = debittransactions_df.to_dict(orient='records')
                    helpers.bulk(es, actions_gen(data, 'transactions'))
                    num_rows = debittransactions_df.shape[0]
            # start importing bank account applications
            bankaccountapplications = BankAccountApplications.objects.filter(user=u.id)

            if bankaccountapplications.count() > 0:
                applications_df = pd.DataFrame()
                geolocator = Nominatim(user_agent="generic-bank-app")  # create a geolocator object
                for app in bankaccountapplications:
                    account_type = app.bankaccounttype.typename
                    record_id = uuid.uuid4()
                    address = {
                        'street': app.streetaddress1 + ' ' + app.streetaddress2,
                        'city': app.suburb,
                        'state': app.province,
                        'country': app.country
                    }

                    application_location = geocode_address(address)

                    if application_location is None:
                        application_location = geolocator.reverse("51.5072, -0.1276")
                    new_row = {
                        'id': record_id,
                        'created_at': app.created_at,
                        'User id': u.id,
                        'Username': u.username,
                        'Full name': u.first_name + ' ' + u.last_name,
                        'Bank Account Type': account_type,
                        'Contact number': app.contactnumber,
                        'Street Address 1': app.streetaddress1,
                        'Street Address 2': app.streetaddress2,
                        'Suburb': app.suburb,
                        'Province': app.province,
                        'Country': app.country,
                        'location': {
                            "lat": application_location['lat'],
                            "lon": application_location['lng']
                        },
                        'Gross income': app.grossincome,
                        'Expenses': app.expenses
                    }
                    applications_df = applications_df.append(new_row, ignore_index=True)
                application_data = applications_df.to_dict(orient='records')
                helpers.bulk(es, actions_gen(application_data, 'account-applications'))

                num_rows = applications_df.shape[0]
