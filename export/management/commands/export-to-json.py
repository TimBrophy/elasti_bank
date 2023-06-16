import time
import requests
from urllib.parse import urlencode
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountApplications
from transactions.models import CreditTransactions, DebitTransactions
from retailers.models import Retailers
from activity.models import Activity
import uuid
import datetime
import re
import pandas as pd
from geopy.geocoders import Nominatim
import warnings
from django.conf import settings
import json
import os
import logging

warnings.filterwarnings("ignore", category=FutureWarning)


def append_to_log_file(filename, new_row):
    # Serialize the dictionary as a JSON string
    new_row_json = json.dumps(new_row)
    print(new_row_json)
    # Get the log directory within the project's base directory
    log_dir = os.path.join(settings.BASE_DIR, 'log_files')
    os.makedirs(log_dir, exist_ok=True)

    # Get the full path to the log file
    filepath = os.path.join(log_dir, filename)
    with open(filepath, "a") as file:
        file.write(new_row_json)
        file.write("\n")


def geocode_address(address):
    default_lat = 44.96
    default_lon = 103.77

    url_params = {
        'address': urlencode(address),
        'key': settings.GOOGLE_MAPS_API_KEY,
    }
    try:
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
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        application_location = (default_lat, default_lon)  # default location
    return application_location


class Command(BaseCommand):
    help = 'Export data to a local JSON file'

    def handle(self, *args, **kwargs):
        users = CustomUser.objects.all()
        # loop through all users

        for u in users:
            # import the users' activities/interactions
            activities = Activity.objects.filter(user=u.id)
            if activities.count() > 0:
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
                    created_at_str = activity.created_at.isoformat()

                    activity_record = {
                        "id": str(record_id),
                        "sor.id": activity.id,
                        "user.id": u.id,
                        "user.email": u.email,
                        "username": u.username,
                        "full_name": u.first_name + ' ' + u.last_name,
                        "created_at": created_at_str,
                        "log_message": activity.activity_log_message,
                        "location": {
                            "lat": activity_location['latitude'],
                            "lon": activity_location['longitude']
                        },
                        "activity_type": activity.activitytype.name
                    }
                    # Append JSON data to file or create new file
                    filename = 'activity_data.log'
                    append_to_log_file(filename, activity_record)

            # loop through all bank accounts for these users
            bankaccounts = BankAccount.objects.filter(user=u.id)
            if bankaccounts.count() > 0:
                # import the bank accounts
                for bankaccount in bankaccounts:
                    record_id = uuid.uuid4()
                    created_at_str = bankaccount.created_at.isoformat()
                    bankaccount_record = {
                        "id": str(record_id),
                        "sor.id": bankaccount.id,
                        "user.id": u.id,
                        "user.email": u.email,
                        "user.name": u.username,
                        "full_name": u.first_name + ' ' + u.last_name,
                        "created_at": created_at_str,
                        "bank_account_type": bankaccount.bankaccounttype.typename,
                        "account_number": str(bankaccount.account_number),
                        "balance": bankaccount.balance
                    }
                    filename = 'bank_account_data.log'
                    append_to_log_file(filename, bankaccount_record)

                    # get all the credit transactions and loop through
                    credittransactions = CreditTransactions.objects.filter(destination_account=bankaccount.id)
                    for ct in credittransactions:
                        created_at_str = bankaccount.created_at.isoformat()
                        timestamp_str = ct.created_at.isoformat()
                        record_id = uuid.uuid4()
                        new_row = {
                            "id": str(record_id),
                            "sor.id": ct.id,
                            "timestamp": timestamp_str,
                            "user.id": u.id,
                            "user.email": u.email,
                            "user.name": u.username,
                            "bank_account": str(bankaccount.account_number),
                            "account_created_date": created_at_str,
                            "full_name": u.first_name + ' ' + u.last_name,
                            "source_entity": ct.source_bank,
                            "source_account": ct.source_account,
                            "sender": ct.from_name,
                            "value": ct.value,
                            "description": ct.description,
                            "text_field": ct.description,
                            "reference": ct.reference,
                            "type": "Credit",
                            "sub_type": ct.transaction_type.name
                        }
                        filename = 'transactions.log'
                        append_to_log_file(filename, new_row)

                    # get all the debit transactions and loop through
                    debittransactions = DebitTransactions.objects.filter(
                        source_account=bankaccount.id)

                    for dt in debittransactions:
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
                        created_at_str = bankaccount.created_at.isoformat()
                        timestamp_str = dt.created_at.isoformat()
                        record_id = uuid.uuid4()
                        new_row = {
                            "id": str(record_id),
                            "sor.id": dt.id,
                            "timestamp": timestamp_str,
                            "user.id": u.id,
                            "user.email": u.email,
                            "user.name": u.username,
                            "bank_account": str(bankaccount.account_number),
                            "account_created_date": created_at_str,
                            "full_name": u.first_name + ' ' + u.last_name,
                            "destination_entity": dt.destination_bank,
                            "destination_account": dt.destination_account,
                            "recipient": dt.recipient_name,
                            "value": dt.value,
                            "description": "{}. Spend category: {}".format(dt.description, category),
                            "text_field": "{}. Spend category: {}".format(dt.description, category),
                            "reference": dt.reference,
                            "type": "Debit",
                            "sub_type": dt.transaction_type.name,
                            "category": category,
                            "location": {
                                "lat": transaction_location["latitude"],
                                "lon": transaction_location["longitude"]
                            }
                        }

                        filename = 'transactions.log'
                        append_to_log_file(filename, new_row)
            # start importing bank account applications
            bankaccountapplications = BankAccountApplications.objects.filter(user=u.id)

            if bankaccountapplications.count() > 0:
                geolocator = Nominatim(user_agent="generic-bank-app")  # create a geolocator object
                for app in bankaccountapplications:
                    account_type = app.bankaccounttype.typename
                    record_id = uuid.uuid4()
                    address = {
                        "street": app.streetaddress1 + ' ' + app.streetaddress2,
                        "city": app.suburb,
                        "state": app.province,
                        "country": app.country
                    }

                    application_location = geocode_address(address)

                    if application_location is None:
                        application_location = geolocator.reverse("51.5072, -0.1276")
                    created_at_str = app.created_at.isoformat()
                    try:
                        new_row = {
                            "id": str(record_id),
                            "sor.id": app.id,
                            "created_at": created_at_str,
                            "user.id": u.id,
                            "user.email": u.email,
                            "user.name": u.username,
                            "full_name": u.first_name + ' ' + u.last_name,
                            "bank_account_type": account_type,
                            "contact_number": app.contactnumber,
                            "street_address_1": app.streetaddress1,
                            "street_address_2": app.streetaddress2,
                            "suburb": app.suburb,
                            "province": app.province,
                            "country": app.country,
                            "location": {
                                "lat": application_location['lat'],
                                "lon": application_location['lng']
                            },
                            "gross_income": app.grossincome,
                            "gross_expenses": app.expenses
                        }
                        filename = 'application_data.log'
                        append_to_log_file(filename, new_row)
                    except:
                        print("Malformed record")
