from django.core.management.base import BaseCommand

from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountType
from transactions.models import CreditTransactions, DebitTransactions, CreditTransactionType, DebitTransactionType
from retailers.models import Retailers

from mimesis import Address, random, Person, Finance, Text, Code
from mimesis.locales import Locale

import random
import string
import datetime
import uuid

finance = Finance(locale=Locale.EN)
code = Code(locale=Locale.EN)
text = Text(locale=Locale.EN)
address = Address(locale=Locale.EN)
person = Person(locale=Locale.EN)

retailers = Retailers.objects.all()
users = CustomUser.objects.all()


def generate_coordinates():
    lat_range = (35.0, 72.0)
    lon_range = (-25.0, 45.0)
    latitude = random.uniform(lat_range[0], lat_range[1])
    longitude = random.uniform(lon_range[0], lon_range[1])
    coordinates_string = "{'longitude' :" + str(longitude) + ", 'latitude' :" + str(latitude) + "}"
    return coordinates_string


def random_created_at():
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = now - datetime.timedelta(days=5)
    time_delta = (now - start_time).total_seconds()
    random_seconds = random.uniform(0, time_delta)
    random_date = start_time + datetime.timedelta(seconds=random_seconds)
    return random_date


def generate_reference():
    characters = string.ascii_letters + string.digits
    ref_string = ''.join(random.choice(characters) for i in range(random.randint(5, 25)))
    return ref_string


class Command(BaseCommand):
    help = 'Generate random bank transactions'

    def add_arguments(self, parser):
        parser.add_argument('total-transaction-count', type=int,
                            help='Indicates the number of transactions to be created')

    def handle(self, *args, **kwargs):
        # get all users in order to loop through and build an account profile

        total_transaction_count = kwargs['total-transaction-count']
        credit_transaction_count = round((total_transaction_count / users.count()) * 0.2)
        debit_transaction_count = round((total_transaction_count / users.count()) * 0.3)
        purchase_transaction_count = round((total_transaction_count / users.count()) * 0.5)

        credit_transaction_type = CreditTransactionType.objects.all()
        debit_transaction_type = DebitTransactionType.objects.exclude(name="Purchase")
        purchase_debit_transaction_type = DebitTransactionType.objects.filter(name="Purchase")

        for instance in users:
            accounts = BankAccount.objects.filter(user=instance.id)
            if accounts:
                counter = 0
                total_credit_amount = random.randint(5000, 100000)

                for i in range(credit_transaction_count):
                    if counter <= credit_transaction_count / 2:
                        source_bank = finance.company()
                        source_account = random.randint(0, 1000000000)
                        value = total_credit_amount / random.randint(2, 3)
                        from_name = person.full_name()
                        destination_account = random.choice(accounts)
                        transaction_type = CreditTransactionType.objects.get(id=1)

                    elif counter > credit_transaction_count / 2:
                        source_account = random.choice(accounts)
                        source_bank = "elasti_bank"
                        from_name = instance.username
                        eligible_accounts = accounts.filter(exclude=source_account)
                        destination_account = random.choice(eligible_accounts)
                        transaction_type = CreditTransactionType.objects.get(id=2)

                    created_at = random_created_at()
                    current_balance = destination_account.balance
                    description = text.quote()
                    reference = generate_reference()
                    CreditTransactions.objects.create(source_account=source_account, source_bank=source_bank,
                                                      from_name=from_name,
                                                      destination_account=destination_account, created_at=created_at,
                                                      value=value, description=description, reference=reference,
                                                      transaction_type=transaction_type)
                    destination_account.balance = current_balance + value
                    destination_account.save()

                for i in range(debit_transaction_count):
                    created_at = random_created_at()
                    source_account = random.choice(accounts)
                    current_balance = source_account.balance
                    destination_bank = finance.company()
                    destination_account = random.randint(0, 1000000000)
                    recipient_name = person.full_name()
                    value = random.randint(50, 1000)
                    description = text.sentence()
                    transaction_type = random.choice(debit_transaction_type)
                    reference = generate_reference()
                    DebitTransactions.objects.create(source_account=source_account, destination_bank=destination_bank,
                                                     destination_account=destination_account,
                                                     recipient_name=recipient_name,
                                                     created_at=created_at,
                                                     value=value, description=description, reference=reference,
                                                     transaction_type=transaction_type)
                    source_account.balance = current_balance + value
                    source_account.save()

                for i in range(purchase_transaction_count):
                    retailer = random.choice(retailers)
                    transaction_description = "{}:{} {} {}".format(retailer.name, text.hex_color(), text.quote(),
                                                                   generate_coordinates())
                    created_at = random_created_at()
                    source_account = random.choice(accounts)
                    current_balance = source_account.balance
                    destination_bank = finance.company()
                    destination_account = random.randint(0, 1000000000)
                    recipient_name = retailer.name
                    value = random.randint(1, 1000)
                    transaction_type = random.choice(purchase_debit_transaction_type)
                    reference = generate_reference()

                    DebitTransactions.objects.create(source_account=source_account, destination_bank=destination_bank,
                                                     destination_account=destination_account,
                                                     recipient_name=recipient_name,
                                                     created_at=created_at,
                                                     value=value, description=transaction_description,
                                                     reference=reference,
                                                     transaction_type=transaction_type)
                    source_account.balance = current_balance + value
                    source_account.save()
