from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import CustomUser, IncomeLevel
from transactions.models import DebitTransactions, DebitTransactionType
from export.models import DebittTransactionExportLog
from bankaccounts.models import BankAccount
from uxtools.models import SpecialOffer
import random
from mimesis import Address, Person, Finance, Text, Code
from mimesis.locales import Locale
import string
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import os
import json
import pytz
from retailers.models import Retailers


finance = Finance(locale=Locale.EN_GB)
code = Code()
text = Text(locale=Locale.EN)
address = Address(locale=Locale.EN)
person = Person(locale=Locale.EN)
retailers = Retailers.objects.all()

def random_created_at(number_of_months):
    utc = pytz.utc
    working_month = datetime.now(tz=timezone.utc) - relativedelta(months=number_of_months)
    year = working_month.year
    month = working_month.month

    last_day = datetime(year, month, 1) + relativedelta(months=1) - timedelta(days=1)

    random_datetime = datetime(year, month, 1) + timedelta(
        days=random.randint(0, (last_day - datetime(year, month, 1)).days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59))
    random_datetime_tz = utc.localize(random_datetime)
    return random_datetime_tz


def generate_reference():
    characters = string.ascii_letters + string.digits
    ref_string = ''.join(random.choice(characters) for i in range(random.randint(5, 25)))
    return ref_string


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


def get_recipient_name(special_offer_search_terms):
    if 'vehicle' in special_offer_search_terms:
        recipient = "Vehicle Finance Bank"
    else:
        recipient = "Generic bank"
    return recipient


class Command(BaseCommand):
    help = 'Generate an transaction scenario in order to trigger special offers'

    def add_arguments(self, parser):
        parser.add_argument('number-of-months', type=int,
                            help='Indicates the number of months to build transactions for')

    def handle(self, *args, **kwargs):
        total_months = kwargs['number-of-months']
        demo_user = CustomUser.objects.filter(username="demo_user").first()
        transaction_account = BankAccount.objects.filter(user=demo_user,
                                                         bankaccounttype__typename='Transmission').first()
        debit_order = DebitTransactionType.objects.filter(name="Debit order").first()
        purchase = DebitTransactionType.objects.filter(name="Purchase").first()
        eft = DebitTransactionType.objects.filter(name="EFT").first()

        # Next step - generate loads of debit orders over the last 12 months
        special_offers = SpecialOffer.objects.all()
        for i in special_offers:
            for t in range(0, total_months):
                recipient_name = get_recipient_name(i.search_terms)
                list_of_terms = i.search_terms.split(',')
                if i.transactiontype.name == 'Debit order':
                    transaction_type = debit_order
                    transaction_description = "Outbound Debit Order - {}. Banking partner: {}".format(
                        random.choice(list_of_terms), recipient_name)
                elif i.transactiontype.name == 'Purchase':
                    transaction_type = purchase
                    retailer = random.choice(retailers)
                    transaction_description = "Purchase made at {} for {}. Banking partner: {}".format(retailer.name,
                                                                                                       random.choice(
                                                                                                           list_of_terms),
                                                                                                       recipient_name)
                else:
                    transaction_type = eft
                    transaction_description = "EFT transfer for {} for {}. Banking partner: {}".format(retailer.name,
                                                                                                       random.choice(
                                                                                                           list_of_terms),
                                                                                                       recipient_name)
                created_at = random_created_at(t)
                target_account = transaction_account
                destination_bank = finance.bank()
                destination_account = "{}_ext".format(random.randint(00000000, 99999999))
                value = random.randint(550, 800)
                search_term_list = i.search_terms.split(',')
                keyword = random.choice(search_term_list)
                reference = generate_reference()
                new_transaction = DebitTransactions.objects.create(source_account=target_account,
                                                                   destination_bank=destination_bank,
                                                                   destination_account=destination_account,
                                                                   recipient_name=recipient_name,
                                                                   created_at=created_at,
                                                                   value=value, description=transaction_description,
                                                                   reference=reference,
                                                                   transaction_type=transaction_type)
                # subtract the value from the source bank account
                transaction_account.balance = transaction_account.balance - value
                transaction_account.save()
                record_id = uuid.uuid4()
                transaction_record = {
                    'id': str(record_id),
                    'sor.id': new_transaction.id,
                    'timestamp': new_transaction.created_at.isoformat(),
                    'user.id': demo_user.id,
                    "user.email": demo_user.email,
                    'user.name': demo_user.username,
                    'bank_account': str(new_transaction.source_account.account_number),
                    'full_name': demo_user.first_name + ' ' + demo_user.last_name,
                    'destination_entity': new_transaction.destination_bank,
                    'destination_account': new_transaction.destination_account,
                    'recipient': new_transaction.recipient_name,
                    'value': new_transaction.value,
                    'description': "{}.".format(new_transaction.description),
                    'text_field': "{}.".format(new_transaction.description),
                    'reference': new_transaction.reference,
                    'type': 'Debit',
                    'sub_type': new_transaction.transaction_type.name,
                    'category': "Special offer demo"
                }
                print(transaction_record)
                filename = "transactions.log"
                append_to_log_file(filename, transaction_record)
