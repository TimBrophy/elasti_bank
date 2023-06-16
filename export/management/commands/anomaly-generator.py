from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import CustomUser, IncomeLevel
from transactions.models import DebitTransactions, DebitTransactionType
from export.models import DebittTransactionExportLog
from bankaccounts.models import BankAccount
import random
from mimesis import Address, Person, Finance, Text, Code
from mimesis.locales import Locale
import string
from datetime import datetime, timezone
import uuid
import os
import json

finance = Finance(locale=Locale.EN_GB)
code = Code()
text = Text(locale=Locale.EN)
address = Address(locale=Locale.EN)
person = Person(locale=Locale.EN)


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

class Command(BaseCommand):
    help = 'Generate an anomaly scenario in order to trigger alerts'

    def add_arguments(self, parser):
        parser.add_argument('scenario', type=str,
                            help='Indicates which scenario needs to be started.')

    def handle(self, *args, **kwargs):
        # create an Elasticsearch client
        # es = Elasticsearch(
        #     cloud_id=settings.ES_CLOUD_ID,
        #     http_auth=(settings.ES_USER, settings.ES_PASS),
        # )
        # define the index and field to search and dedupe on
        scenario = kwargs['scenario']

        if scenario == "exfiltration":
            # select random user to drain the bank account of
            high_income = IncomeLevel.objects.get(category="high")
            victims = []
            num_victims = random.randrange(1, 5)
            counter = 0
            while counter <= num_victims:
                victim = random.choice(CustomUser.objects.filter(income_level=high_income))
                victims.append(victim)
                counter = counter + 1
            for target in victims:
                accounts = BankAccount.objects.filter(user=target)
                if len(accounts) > 1:
                    target_account = random.choice(accounts)
                else:
                    target_account = accounts.first()
                if target_account:
                    increment = (target_account.balance - random.randint(10, 50)) / (target_account.balance * 1.2)
                    number_debits = round(target_account.balance / increment)
                    debit_transaction_type = DebitTransactionType.objects.filter(name="EFT").first()
                    for i in range(number_debits):
                        recipient_name = "Anonymous hacker"
                        destination_bank = "Bad guy bank"
                        destination_account = "123456789"
                        created_at = datetime.now(tz=timezone.utc)
                        value = increment
                        description = "{}. Outbound EFT to {}".format(text.sentence(), recipient_name)
                        reference = generate_reference()
                        transaction_type = debit_transaction_type
                        current_balance = target_account.balance
                        new_transaction = DebitTransactions.objects.create(source_account=target_account,
                                                                           destination_bank=destination_bank,
                                                                           destination_account=destination_account,
                                                                           recipient_name=recipient_name,
                                                                           created_at=created_at,
                                                                           value=value, description=description,
                                                                           reference=reference,
                                                                           transaction_type=transaction_type)
                        # subtract the value from the source bank account
                        target_account.balance = current_balance - value
                        target_account.save()
                        record_id = uuid.uuid4()
                        transaction_record = {
                            'id': str(record_id),
                            'sor.id': new_transaction.id,
                            'timestamp': new_transaction.created_at.isoformat(),
                            'user.id': target.id,
                            "user.email": target.email,
                            'user.name': target.username,
                            'bank_account': str(new_transaction.source_account.account_number),
                            'full_name': target.first_name + ' ' + target.last_name,
                            'destination_entity': new_transaction.destination_bank,
                            'destination_account': new_transaction.destination_account,
                            'recipient': new_transaction.recipient_name,
                            'value': new_transaction.value,
                            'description': "{}. Spend category: Exfiltration".format(new_transaction.description),
                            'reference': new_transaction.reference,
                            'type': 'Debit',
                            'sub_type': new_transaction.transaction_type.name,
                            'category': "Exfiltration"
                        }
                        filename = "transactions.log"
                        append_to_log_file(filename, transaction_record)
                        # es.create(index='transactions', id=record_id, document=transaction_record)
                        log_entry = DebittTransactionExportLog(id=new_transaction.id,
                                                               exported_at=datetime.now(tz=timezone.utc))
                        log_entry.save()
                        print("Added new debit transaction of type: {}".format(new_transaction.transaction_type))
