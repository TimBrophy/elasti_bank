from django.shortcuts import render
from content.models import ContentItem
from activity.models import Activity, ActivityType
from bankaccounts.models import BankAccount, BankAccountType
from transactions.models import CreditTransactions, DebitTransactions
from .forms import ContactForm
from datetime import datetime, timezone, timedelta


# Create your views.py here.


def home(request):
    featured = ContentItem.objects.filter(featured=1)
    form = ContactForm()
    net_worth = 0
    my_accounts = []
    most_recent_transactions = []
    if request.user.is_authenticated:
        my_accounts = BankAccount.objects.filter(user=request.user).order_by('-created_at')
        my_account_ids = my_accounts.values_list('id', flat=True)

        for i in my_accounts:
            current = i.balance
            net_worth = net_worth + current

        # Filter credit and debit transactions for the bank account id
        credit_transactions = CreditTransactions.objects.filter(destination_account__in=my_accounts).order_by(
            '-created_at')
        debit_transactions = DebitTransactions.objects.filter(source_account__in=my_accounts).order_by(
            '-created_at')

        # Combine credit and debit transactions

        credit_transactions = list(credit_transactions)
        debit_transactions = list(debit_transactions)
        transactions = credit_transactions + debit_transactions
        for transaction in transactions:
            if isinstance(transaction, DebitTransactions):
                transaction.value = -abs(transaction.value)
        # Sort transactions by transaction date and time
        transactions.sort(key=lambda x: x.created_at, reverse=True)

        most_recent_transactions = transactions[:10]

        activity_log_message = "Viewed: home page"
        activity_type = ActivityType.objects.get(id=1)
        activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                                  created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
        activity_entry.save()

    bankaccounttypes = BankAccountType.objects.all()

    return render(request, 'home.html', {'featured_list': featured, 'form': form, 'net_worth': net_worth,
                                         'bankaccounttypes_list': bankaccounttypes, 'my_accounts': my_accounts,
                                         'transactions': most_recent_transactions})
