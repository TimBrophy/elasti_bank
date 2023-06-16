from django.core.management.base import BaseCommand, CommandError
from bankaccounts.models import BankAccount, BankAccountType, BankAccountApplicationStatus
from accounts.models import IncomeLevel
from transactions.models import CreditTransactions, CreditTransactionType, DebitTransactions, DebitTransactionType
from activity.models import ActivityType


class Command(BaseCommand):
    help = 'Complete master data setup'

    def add_arguments(self, parser):
        # Add any additional arguments here if needed
        pass

    def handle(self, *args, **options):
        activity_types = ['Website', 'Retail bank', 'ATM']
        for i in activity_types:
            ActivityType.objects.create(name=i)

        bank_account_types = ['Fixed deposit', 'Savings', 'Loan', 'Credit', 'Investment', 'Transmission']
        for i in bank_account_types:
            BankAccountType.objects.create(typename=i)

        bank_account_application_status = ['Approved', 'In progress', 'Submitted']
        for i in bank_account_application_status:
            BankAccountApplicationStatus.objects.create(statusname=i)

        income_level_data = [
            {
                'category': 'high',
                'upper': 20000,
                'lower': 12000
            },
            {
                'category': 'middle',
                'upper': 11000,
                'lower': 6000
             },
            {
                'category': 'low',
                'upper': 6000,
                'lower': 2000
             }
        ]

        for i in income_level_data:
            IncomeLevel.objects.create(**i)

        credit_transaction_types = ['Transfer', 'EFT']
        for i in credit_transaction_types:
            CreditTransactionType.objects.create(name=i)

        debit_transaction_types = ['Transfer', 'Debit order', 'EFT', 'Purchase']
        for i in debit_transaction_types:
            DebitTransactionType.objects.create(name=i)