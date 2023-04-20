from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from bankaccounts.models import BankAccount, BankAccountType, BankAccountApplications
from mimesis import Address, random, Person
from mimesis.locales import Locale
import random
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from random_address import real_random_address


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

class Command(BaseCommand):
    help = 'Generate random bank accounts and account applications'

    def add_arguments(self, parser):
        parser.add_argument('number-of-months', type=int,
                            help='Indicates the number of months to build accounts and applications for')

    def handle(self, *args, **kwargs):
        account_users = CustomUser.objects.exclude(id=1)
        account_types = BankAccountType.objects.all()
        total_months = kwargs['number-of-months']
        transmission_accounts = BankAccountType.objects.filter(typename='Transmission')
        savings_accounts = BankAccountType.objects.filter(typename='Savings')
        loan_accounts =BankAccountType.objects.filter(typename='Loan')
        fixed_deposit_accounts = BankAccountType.objects.filter(typename='Fixed deposit')
        investment_accounts = BankAccountType.objects.filter(typename='Investment')
        credit_accounts = BankAccountType.objects.filter(typename='Credit')
        inbound_credit_accounts = list(transmission_accounts) + list(savings_accounts)
        outbound_purchase_accounts = list(transmission_accounts) + list(credit_accounts)
        outbound_transfer_accounts = list(transmission_accounts) + list(savings_accounts) + list(loan_accounts)
        inbound_internal_transfer_accounts = list(fixed_deposit_accounts) + list(savings_accounts) + list(
            loan_accounts) + list(investment_accounts) + list(credit_accounts)
        outbound_internal_transfer_accounts = list(transmission_accounts) + list(savings_accounts)

        for a in account_users:
            number_of_accounts = random.randrange(1, 5)
            app_probability = random.randrange(0, 6)

            for accountnum in range(number_of_accounts):
                # does the user have a valid inbound account yet?
                user_inbound_accounts = BankAccount.objects.filter(user=a.id, bankaccounttype__typename__in=inbound_credit_accounts)
                if not user_inbound_accounts:
                    account_type = random.choice(inbound_credit_accounts)
                    account_type = BankAccountType.objects.get(typename=account_type)
                else:
                    account_type = random.choice(account_types)
                random_month = random.randrange(1, total_months)
                account_user = a

                timestamp = random_created_at(random_month)
                BankAccount.objects.create(user=account_user, bankaccounttype=account_type, created_at=timestamp,
                                           balance=0)

            address = Address(locale=Locale.EN)
            if app_probability > 4:

                new_address = real_random_address()

                if not new_address['city']:
                    new_address = real_random_address()
                else:
                    for applicationnum in range(random.randint(1, 3)):
                        random_month = random.randrange(1, total_months)

                        account_user = random.choice(account_users)
                        account_type = random.choice(account_types)
                        app_timestamp = random_created_at(random_month)
                        address1 = new_address['address1']
                        address2 = new_address['address2']
                        suburb = new_address['city']
                        province = new_address['state']
                        country = 'United States'
                        grossincome = random.randint(5000, 25000)
                        expenses = random.randint(5000, 25000)

                    BankAccountApplications.objects.create(user=account_user, bankaccounttype=account_type,
                                                           created_at=app_timestamp,
                                                           contactnumber=random.randint(0000000, 9999999),
                                                           streetaddress1=address1,
                                                           streetaddress2=address2, suburb=suburb, province=province,
                                                           country=country,
                                                           grossincome=grossincome, expenses=expenses)
