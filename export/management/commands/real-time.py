from django.core.management.base import BaseCommand
import random
from django.conf import settings
import time
from datetime import datetime, timezone
from accounts.models import CustomUser, IncomeLevel
from bankaccounts.models import BankAccount, BankAccountApplications, BankAccountType
from transactions.models import CreditTransactions, DebitTransactions, CreditTransactionType, DebitTransactionType
from export.models import CreditTransactionExportLog, DebittTransactionExportLog
from retailers.models import Retailers
from activity.models import Activity, ActivityType
from mimesis import Person, Finance, Text, Code
from mimesis.locales import Locale
import string
from random_address import real_random_address, random_address
from elasticsearch import Elasticsearch, helpers
import uuid
from urllib.parse import urlencode
import requests
from geopy.geocoders import Nominatim
import re
import json
import os

person = Person(Locale.EN)
finance = Finance(Locale.EN)
text = Text()
retailers = Retailers.objects.all()
code = Code()

def geocode_address(address):
    default_lat = 44.96
    default_lon = 103.77

    try:
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
            raise requests.HTTPError(response.status_code)

    except (requests.RequestException, requests.HTTPError, KeyError):
        application_location = (default_lat, default_lon)  # default location

    return application_location

def generate_coordinates():
    address = random_address.real_random_address()
    latitude = address['coordinates']['lat']
    longitude = address['coordinates']['lng']
    coordinates_string = "{'longitude' :" + str(longitude) + ", 'latitude' :" + str(latitude) + "}"
    return coordinates_string

def generate_reference():
    characters = string.ascii_letters + string.digits
    ref_string = ''.join(random.choice(characters) for i in range(random.randint(5, 25)))
    return ref_string

def create_random_transaction(user, category):
    purchase_debit_transaction_type = DebitTransactionType.objects.filter(name="Purchase")
    credit_transaction_type = CreditTransactionType.objects.all()
    debit_transaction_type = DebitTransactionType.objects.exclude(name="Purchase")

    if category == "high":
        credit_transaction_range = [15000, 40000]
        debit_transaction_range = [2000, 10000]
        purchase_transaction_range = [10, 4000]
        transfer_transaction_range = [500, 5000]

    elif category == "middle":
        credit_transaction_range = [7000, 15000]
        debit_transaction_range = [500, 3000]
        purchase_transaction_range = [10, 1000]
        transfer_transaction_range = [200, 800]

    else:
        credit_transaction_range = [1500, 5000]
        debit_transaction_range = [150, 500]
        purchase_transaction_range = [1, 150]
        transfer_transaction_range = [50, 600]

    transaction_choice = random.randint(1, 100)
    accounts = BankAccount.objects.filter(user=user)
    transmission_accounts = accounts.filter(bankaccounttype__typename='Transmission')
    savings_accounts = accounts.filter(bankaccounttype__typename='Savings')
    loan_accounts = accounts.filter(bankaccounttype__typename='Loan')
    fixed_deposit_accounts = accounts.filter(bankaccounttype__typename='Fixed deposit')
    investment_accounts = accounts.filter(bankaccounttype__typename='Investment')
    credit_accounts = accounts.filter(bankaccounttype__typename='Credit')
    inbound_credit_accounts = list(transmission_accounts) + list(savings_accounts)
    outbound_purchase_accounts = list(transmission_accounts) + list(credit_accounts)
    outbound_transfer_accounts = list(transmission_accounts) + list(savings_accounts) + list(loan_accounts)
    inbound_internal_transfer_accounts = list(fixed_deposit_accounts) + list(savings_accounts) + list(
        loan_accounts) + list(investment_accounts) + list(credit_accounts)
    outbound_internal_transfer_accounts = list(transmission_accounts) + list(savings_accounts)

    if transaction_choice < 10:
        # incoming credit
        if len(inbound_credit_accounts):
            source_account = "{}_ext".format(random.randint(00000000, 99999999))
            source_bank = finance.bank()
            from_name = finance.company()
            destination_account = random.choice(inbound_credit_accounts)
            created_at = datetime.now(tz=timezone.utc)
            value = random.randint(credit_transaction_range[0], credit_transaction_range[1])
            description = "{}. Inbound EFT from {}.".format(text.sentence(), from_name)
            reference = generate_reference()
            transaction_type = random.choice(credit_transaction_type)
            new_transaction = CreditTransactions.objects.create(source_account=source_account, source_bank=source_bank,
                                              from_name=from_name,
                                              destination_account=destination_account,
                                              created_at=created_at,
                                              value=value, description=description, reference=reference,
                                              transaction_type=transaction_type)
            # add the value from the source bank account to the destination account
            current_balance = destination_account.balance
            destination_account.balance = current_balance + value
            destination_account.save()
            return new_transaction

    elif transaction_choice > 80:
        # outgoing eft
        if len(outbound_transfer_accounts):
            source_account = random.choice(outbound_transfer_accounts)
            recipient_name = person.full_name()
            destination_bank = finance.bank()
            destination_account = "{}_ext".format(random.randint(00000000, 99999999))
            created_at = datetime.now(tz=timezone.utc)
            value = random.randint(debit_transaction_range[0], debit_transaction_range[1])
            description = "{}. Outbound EFT to {}".format(text.sentence(), recipient_name)
            reference = generate_reference()
            transaction_type = random.choice(debit_transaction_type)
            current_balance = source_account.balance
            source_account.balance = current_balance - value
            new_transaction = DebitTransactions.objects.create(source_account=source_account,
                                             destination_bank=destination_bank,
                                             destination_account=destination_account,
                                             recipient_name=recipient_name,
                                             created_at=created_at,
                                             value=value, description=description, reference=reference,
                                             transaction_type=transaction_type)
            # subtract the value from the source bank account
            source_account.balance = current_balance - value
            source_account.save()
            return new_transaction
    else:
        # purchase
        if len(outbound_purchase_accounts):
            retailer = random.choice(retailers)
            transaction_description = "Purchase at {}:{} {} {}".format(retailer.name, text.hex_color(), code.isbn(),
                                                                       generate_coordinates())
            created_at = datetime.now(tz=timezone.utc)
            source_account = random.choice(outbound_purchase_accounts)
            current_balance = source_account.balance
            destination_bank = finance.bank()
            destination_account = "{}_retail".format(random.randint(00000000, 99999999))
            recipient_name = retailer.name
            value = random.randint(purchase_transaction_range[0], purchase_transaction_range[1])
            transaction_type = random.choice(purchase_debit_transaction_type)
            reference = generate_reference()

            new_transaction = DebitTransactions.objects.create(source_account=source_account,
                                             destination_bank=destination_bank,
                                             destination_account=destination_account,
                                             recipient_name=recipient_name,
                                             created_at=created_at,
                                             value=value, description=transaction_description,
                                             reference=reference,
                                             transaction_type=transaction_type)
            source_account.balance = current_balance - value
            source_account.save()
            return new_transaction


def create_random_bankaccount_application(user):
    account_types = BankAccountType.objects.all()
    account_type = random.choice(account_types)
    new_address = real_random_address()
    if not 'city' in new_address:
        new_address = real_random_address()
    address1 = new_address['address1']
    address2 = new_address['address2']
    suburb = new_address['city']
    province = new_address['state']
    country = 'United States'
    grossincome = random.randint(5000, 25000)
    expenses = random.randint(5000, 25000)


    account_application = BankAccountApplications.objects.create(user=user, bankaccounttype=account_type,
                                       created_at=datetime.now(tz=timezone.utc),
                                       contactnumber=random.randint(0000000, 9999999),
                                       streetaddress1=address1,
                                       streetaddress2=address2, suburb=suburb, province=province,
                                       country=country,
                                       grossincome=grossincome, expenses=expenses)
    return account_application

def create_random_bankaccount(user):
    account_types = BankAccountType.objects.all()
    account_type = random.choice(account_types)
    new_bank_account = BankAccount.objects.create(user=user, bankaccounttype=account_type, created_at=datetime.now(tz=timezone.utc),
                                                  balance=0)
    return new_bank_account

def update_random_bankaccount(user):
    accounts = BankAccount.objects.filter(user=user)
    if len(accounts):
        chosen_account = random.choice(accounts)
        return chosen_account

def create_random_user():
    # define the users' income level
    income_level = random.randint(1, 8)
    if income_level >= 7:
        income_category = IncomeLevel.objects.get(id=3)
    elif 3 <= income_level <= 6:
        income_category = IncomeLevel.objects.get(id=2)
    else:
        income_category = IncomeLevel.objects.get(id=1)
    username = person.username()
    first_name = person.first_name()
    last_name = person.last_name()
    email = person.email()
    password = random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    new_user = CustomUser.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email,
                                   password=password, income_level=income_category)
    return new_user

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



class Command(BaseCommand):
    help = 'Generate random data in real time to simulate a live banking environment'

    def add_arguments(self, parser):
        parser.add_argument('number-of-minutes', type=int,
                            help='Indicates the number of minutes that the script should run for before shutting down')

    def handle(self, *args, **kwargs):
        total_minutes = kwargs['number-of-minutes']
        start_time = time.time()
        while (time.time() - start_time) < total_minutes * 60:
            print("New loop.")
            es = Elasticsearch(
                cloud_id=settings.ES_CLOUD_ID,
                http_auth=(settings.ES_USER, settings.ES_PASS),
            )
            # determine if this is a new customer or existing customer
            new_or_update_user = random.randint(1,100)
            if new_or_update_user < 20:
                new_user = create_random_user()
                print("Added a new user: {}".format(new_user.username))
            else:
                users = CustomUser.objects.all()
                current_user = random.choice(users)
                random_activity_type = random.randrange(1, 1000)
                description = text.quote()
                created_at = datetime.now(tz=timezone.utc)
                rand_location = generate_coordinates()

                if random_activity_type < 50:
                    activity_type = ActivityType.objects.filter(name="Retail bank").first()

                elif 50 <= random_activity_type <= 200:
                    activity_type = ActivityType.objects.filter(name="ATM").first()

                else:
                    activity_type = ActivityType.objects.filter(name="Website").first()

                new_activity = Activity.objects.create(activitytype=activity_type, user=current_user, created_at=created_at,
                                        activity_log_message=description, location=rand_location)

                target_string = str(new_activity.location)
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
                created_at_str = new_activity.created_at.isoformat()

                activity_record = {
                    "id": str(record_id),
                    "sor.id": new_activity.id,
                    "user.id": current_user.id,
                    "user.email": current_user.email,
                    "user.name": current_user.username,
                    "full_name": current_user.first_name + ' ' + current_user.last_name,
                    "created_at": created_at_str,
                    "log_message": new_activity.activity_log_message,
                    "location": {
                        "lat": activity_location['latitude'],
                        "lon": activity_location['longitude']
                    },
                    "activity_type": new_activity.activitytype.name
                }
                # Append JSON data to file or create new file
                filename = 'activity_data.log'
                append_to_log_file(filename, activity_record)


                new_or_update_bankaccount = random.randint(1, 100)
                if new_or_update_bankaccount < 20:
                    if new_or_update_bankaccount < 5:
                        # create new bank account
                        new_account = create_random_bankaccount(current_user)
                        record_id = uuid.uuid4()
                        bankaccount_record = {
                            "id": str(record_id),
                            "sor.id": new_account.id,
                            "user.id": current_user.id,
                            "user.email": current_user.email,
                            "user.name": current_user.username,
                            "full_name": current_user.first_name + ' ' + current_user.last_name,
                            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                            "created_at": new_account.created_at.isoformat(),
                            "bank_account_type": new_account.bankaccounttype.typename,
                            "account_number": str(new_account.account_number),
                            "balance": new_account.balance
                        }
                        # es.create(index='bank-accounts',id=record_id, document=bankaccount_record)
                        filename = "bank_account_data.log"
                        append_to_log_file(filename, bankaccount_record)
                        print("Added a new bank account: {}".format(new_account.account_number))
                    else:
                        updated_account = update_random_bankaccount(current_user)
                        if updated_account:
                            record_id = uuid.uuid4()
                            bankaccount_record = {
                                "id": str(record_id),
                                "sor.id": updated_account.id,
                                "user.id": current_user.id,
                                "user.email": current_user.email,
                                "user.name": current_user.username,
                                "full_name": current_user.first_name + ' ' + current_user.last_name,
                                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                                "created_at": updated_account.created_at.isoformat(),
                                "bank_account_type": updated_account.bankaccounttype.typename,
                                "account_number": str(updated_account.account_number),
                                "balance": updated_account.balance
                            }
                            filename = 'bank_account_data.log'
                            append_to_log_file(filename, bankaccount_record)
                            # es.create(index='bank-accounts',id=record_id, document=bankaccount_record)
                            print("Updated an existing bank account: {}".format(updated_account.account_number))
                elif new_or_update_bankaccount > 80:
                    # create new bank account application
                    new_application = create_random_bankaccount_application(current_user)
                    account_type = new_application.bankaccounttype.typename
                    record_id = uuid.uuid4()
                    address = {
                        "street": new_application.streetaddress1 + ' ' + new_application.streetaddress2,
                        "city": new_application.suburb,
                        "state": new_application.province,
                        "country": new_application.country
                    }

                    application_location = geocode_address(address)
                    geolocator = Nominatim(user_agent="generic-bank-app")
                    if application_location is None:
                        application_location = geolocator.reverse("51.5072, -0.1276")
                    bankaccount_application_record = {
                        "id": str(record_id),
                        "sor.id": new_application.id,
                        "created_at": new_application.created_at.isoformat(),
                        "user.id": current_user.id,
                        "user.email": current_user.email,
                        "user.name": current_user.username,
                        "full_name": current_user.first_name + ' ' + current_user.last_name,
                        "bank_account_type": account_type,
                        "contact_number": str(new_application.contactnumber),
                        "street_address_1": new_application.streetaddress1,
                        "street_address_2": new_application.streetaddress2,
                        "suburb": new_application.suburb,
                        "province": new_application.province,
                        "country": new_application.country,
                        "location": {
                            "lat": application_location['lat'],
                            "lon": application_location['lng']
                        },
                        "gross_income": new_application.grossincome,
                        "gross_expenses": new_application.expenses
                    }
                    filename = "application_data.log"
                    append_to_log_file(filename, bankaccount_application_record)
                    # es.create(index='account-applications', id=record_id, document=bankaccount_application_record)
                    print("Added a new bank account application for {}, {}".format(current_user.username, account_type))
                else:
                    # add transactions to an existing account

                    new_transaction = create_random_transaction(current_user, current_user.income_level.category)
                    if new_transaction:
                        if new_transaction.transaction_type in DebitTransactionType.objects.all():
                            retailers = Retailers.objects.filter(name=new_transaction.recipient_name)
                            if retailers.exists():
                                category = retailers.first().dominant_operational_format
                            else:
                                category = "Unspecified"
                            if new_transaction.transaction_type.name == "Purchase":
                                # Regular expression to extract the latitude and longitude values
                                pattern = r"'longitude'\s*:\s*([-+]?\d*\.\d+|\d+).*'latitude'\s*:\s*([-+]?\d*\.\d+|\d+)"
                                # Find the latitude and longitude values in the input string
                                match = re.search(pattern, new_transaction.description)
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
                            transaction_record = {
                                "id": str(record_id),
                                "sor.id": new_transaction.id,
                                "timestamp": new_transaction.created_at.isoformat(),
                                "user.id": current_user.id,
                                "user.email": current_user.email,
                                "user.name": current_user.username,
                                "bank_account": str(new_transaction.source_account.account_number),
                                "full_name": current_user.first_name + ' ' + current_user.last_name,
                                "destination_entity": new_transaction.destination_bank,
                                "destination_account": new_transaction.destination_account,
                                "recipient": new_transaction.recipient_name,
                                "value": new_transaction.value,
                                "description": "{}. Spend category: {}".format(new_transaction.description, category),
                                "text_field": "{}. Spend category: {}".format(new_transaction.description, category),
                                "reference": new_transaction.reference,
                                "type": 'Debit',
                                "sub_type": new_transaction.transaction_type.name,
                                "category": category,
                                "location": {
                                    "lat": transaction_location["latitude"],
                                    "lon": transaction_location["longitude"]
                                }
                            }
                            filename = "transactions.log"
                            append_to_log_file(filename, transaction_record)
                            # es.create(index='transactions', id=record_id, document=transaction_record)
                            log_entry = DebittTransactionExportLog(id=new_transaction.id,
                                                                   exported_at=datetime.now(tz=timezone.utc))
                            log_entry.save()
                            print("Added new debit transaction of type: {}".format(new_transaction.transaction_type))

                        elif new_transaction.transaction_type in CreditTransactionType.objects.all():
                            record_id = uuid.uuid4()
                            transaction_record = {
                                "id": str(record_id),
                                "sor.id": new_transaction.id,
                                "timestamp": new_transaction.created_at.isoformat(),
                                "user.id": current_user.id,
                                "user.email": current_user.email,
                                "user.name": current_user.username,
                                "bank_account": str(new_transaction.destination_account.account_number),
                                "full_name": current_user.first_name + ' ' + current_user.last_name,
                                "source_entity": new_transaction.source_bank,
                                "source_account": new_transaction.source_account,
                                "sender": new_transaction.from_name,
                                "value": new_transaction.value,
                                "description": new_transaction.description,
                                "text_field": new_transaction.description,
                                "reference": new_transaction.reference,
                                "type": "Credit",
                                "sub_type": new_transaction.transaction_type.name
                            }
                            filename = "transactions.log"
                            append_to_log_file(filename, transaction_record)
                            log_entry = CreditTransactionExportLog(id=new_transaction.id,
                                                                   exported_at=datetime.now(tz=timezone.utc))
                            log_entry.save()
                            # es.create(index='transactions', id=record_id, document=transaction_record)
                            print("Added new credit transaction.")

            print("Waiting...")
            time.sleep(30)