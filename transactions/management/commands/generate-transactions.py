import random
import string
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from mimesis import Address, Person, Finance, Text, Code
from mimesis.locales import Locale
import pandas as pd
import pytz
import random_address
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountType
from transactions.models import CreditTransactions, DebitTransactions, CreditTransactionType, DebitTransactionType
from retailers.models import Retailers
import json

finance = Finance(locale=Locale.EN_GB)
code = Code()
text = Text(locale=Locale.EN)
address = Address(locale=Locale.EN)
person = Person(locale=Locale.EN)


def random_description():
    payment_topics = ['gifts', 'mobile phone', 'school fees', 'cleaner', 'babysitting', 'contractors', 'gym', 'repairs']
    word = random.choice(payment_topics)
    return word


def generate_coordinates():
    address = random_address.real_random_address()
    latitude = address['coordinates']['lat']
    longitude = address['coordinates']['lng']
    coordinates_string = "{'longitude' :" + str(longitude) + ", 'latitude' :" + str(latitude) + "}"
    return coordinates_string


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


class Command(BaseCommand):
    help = 'Generate random bank transactions'

    def add_arguments(self, parser):
        parser.add_argument('number-of-months', type=int,
                            help='Indicates the number of months to build transactions for')

    def handle(self, *args, **kwargs):
        retailers = Retailers.objects.all()
        users = CustomUser.objects.all()

        purchase_debit_transaction_type = DebitTransactionType.objects.filter(name="Purchase")
        credit_transaction_type = CreditTransactionType.objects.all()
        debit_transaction_type = DebitTransactionType.objects.exclude(name="Purchase")

        total_months = kwargs['number-of-months']
        complete_value_df = pd.DataFrame(columns=['type', 'amount'])
        complete_value_data = []
        for u in users:

            if u.income_level.category == "high":
                credit_transaction_range = [15000, 40000]
                debit_transaction_range = [2000, 10000]
                purchase_transaction_range = [10, 4000]
                transfer_transaction_range = [500, 5000]

            elif u.income_level.category == "middle":
                credit_transaction_range = [7000, 15000]
                debit_transaction_range = [500, 3000]
                purchase_transaction_range = [10, 1000]
                transfer_transaction_range = [200, 800]

            else:
                credit_transaction_range = [1500, 5000]
                debit_transaction_range = [150, 500]
                purchase_transaction_range = [1, 150]
                transfer_transaction_range = [50, 600]

            accounts = BankAccount.objects.filter(user=u.id)
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
            if accounts:
                for i in range(0, total_months):

                    total_credit_transactions = random.randint(1, 3)
                    total_internal_transfers = random.randint(1, 3)
                    total_debit_transactions = random.randint(1, 5)
                    total_purchase_transactions = random.randint(8, 17)

                    credit_df = pd.DataFrame(columns=['type', 'amount'])
                    # generate credits from EXTERNAL
                    # first test if this user has inbound credit accounts
                    if len(inbound_credit_accounts):
                        credit_data = []
                        for ct in range(total_credit_transactions):
                            source_account = "{}_ext".format(random.randint(00000000, 99999999))
                            source_bank = finance.bank()
                            from_name = finance.company()
                            destination_account = random.choice(inbound_credit_accounts)
                            created_at = random_created_at(i)
                            value = random.randint(credit_transaction_range[0], credit_transaction_range[1])
                            description = "Inbound EFT from {} for {}.".format(from_name, random_description())
                            reference = generate_reference()
                            transaction_type = random.choice(credit_transaction_type)
                            CreditTransactions.objects.create(source_account=source_account, source_bank=source_bank,
                                                              from_name=from_name,
                                                              destination_account=destination_account,
                                                              created_at=created_at,
                                                              value=value, description=description, reference=reference,
                                                              transaction_type=transaction_type)
                            # add the value from the source bank account to the destination account
                            current_balance = destination_account.balance
                            destination_account.balance = current_balance + value
                            destination_account.save()
                            credit_data.append({'type': 'credit', 'amount': value})
                            credit_df = pd.concat([credit_df, pd.DataFrame(credit_data)])

                        debit_df = pd.DataFrame(columns=['type', 'amount'])

                    # generate EXTERNAL transfers
                    # first test if this user as accounts that can be used to send money from
                    if len(outbound_transfer_accounts):
                        debit_data = []
                        for dt in range(total_debit_transactions):
                            source_account = random.choice(outbound_transfer_accounts)
                            # source_account = BankAccount.objects.get(id=source_account)
                            recipient_name = person.full_name()
                            destination_bank = finance.bank()
                            destination_account = "{}_ext".format(random.randint(00000000, 99999999))
                            created_at = random_created_at(i)
                            value = random.randint(debit_transaction_range[0], debit_transaction_range[1])
                            description = "Outbound EFT to {} for {}".format(recipient_name, random_description())
                            reference = generate_reference()
                            transaction_type = random.choice(debit_transaction_type)
                            current_balance = source_account.balance
                            source_account.balance = current_balance - value
                            DebitTransactions.objects.create(source_account=source_account,
                                                             destination_bank=destination_bank,
                                                             destination_account=destination_account,
                                                             recipient_name=recipient_name,
                                                             created_at=created_at,
                                                             value=value, description=description, reference=reference,
                                                             transaction_type=transaction_type)
                            # subtract the value from the source bank account
                            source_account.balance = current_balance - value
                            source_account.save()
                            debit_data.append({'type': 'debit', 'amount': value})
                            debit_df = pd.concat([debit_df, pd.DataFrame(debit_data)])

                    # generate EXTERNAL purchases
                    # first test if this user actually has an account that can do purchases
                    if len(outbound_purchase_accounts):
                        purchase_df = pd.DataFrame(columns=['type', 'amount'])
                        purchase_data = []
                        for pt in range(total_purchase_transactions):
                            retailer = random.choice(retailers)
                            transaction_description = "Purchase at {}:{} {} {}".format(retailer.name, text.hex_color(),
                                                                                       code.isbn(),
                                                                                       generate_coordinates())
                            created_at = random_created_at(i)
                            source_account = random.choice(outbound_purchase_accounts)
                            current_balance = source_account.balance
                            destination_bank = finance.bank()
                            destination_account = "{}_retail".format(random.randint(00000000, 99999999))
                            recipient_name = retailer.name
                            value = random.randint(purchase_transaction_range[0], purchase_transaction_range[1])
                            transaction_type = random.choice(purchase_debit_transaction_type)
                            reference = generate_reference()

                            DebitTransactions.objects.create(source_account=source_account,
                                                             destination_bank=destination_bank,
                                                             destination_account=destination_account,
                                                             recipient_name=recipient_name,
                                                             created_at=created_at,
                                                             value=value, description=transaction_description,
                                                             reference=reference,
                                                             transaction_type=transaction_type)
                            source_account.balance = current_balance - value
                            source_account.save()
                            purchase_data.append({'type': 'debit', 'amount': value})
                            purchase_df = pd.concat([purchase_df, pd.DataFrame(purchase_data)])

                    # generate INTERNAL transfers
                    transfer_df = pd.DataFrame(columns=['type', 'amount'])
                    transfer_data = []
                    if len(inbound_internal_transfer_accounts) > 1:
                        for it in range(total_internal_transfers):
                            # handle the credit to the other account
                            source_account = random.choice(outbound_internal_transfer_accounts)
                            source_bank = "elasti_bank"
                            from_name = u.username
                            destination_account = random.choice(inbound_internal_transfer_accounts)
                            while destination_account == source_account:
                                destination_account = random.choice(inbound_internal_transfer_accounts)
                            this_credit_transaction_type = credit_transaction_type.filter(name="Transfer").first()
                            this_debit_transaction_type = debit_transaction_type.filter(name="Transfer").first()

                            created_at = random_created_at(i)
                            value = random.randint(transfer_transaction_range[0], transfer_transaction_range[1])
                            description = "Internal transfer for {}".format(random_description())
                            reference = generate_reference()

                            CreditTransactions.objects.create(source_account=source_account, source_bank=source_bank,
                                                              from_name=from_name,
                                                              destination_account=destination_account,
                                                              created_at=created_at,
                                                              value=value, description=description, reference=reference,
                                                              transaction_type=this_credit_transaction_type)
                            # add the value from the source bank account
                            current_balance = destination_account.balance
                            destination_account.balance = current_balance + value
                            destination_account.save()

                            # handle the debit from the source account
                            DebitTransactions.objects.create(source_account=source_account,
                                                             destination_bank=source_bank,
                                                             destination_account=destination_account,
                                                             recipient_name=from_name,
                                                             created_at=created_at,
                                                             value=value, description=description,
                                                             reference=reference,
                                                             transaction_type=this_debit_transaction_type)

                            # subtract the value from the source bank account
                            source_balance = source_account.balance
                            source_account.balance = source_balance - value
                            source_account.save()

                            transfer_data.append({'type': 'debit', 'amount': value})
                            transfer_df = pd.concat([transfer_df, pd.DataFrame(transfer_data)])
