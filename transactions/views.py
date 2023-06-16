from django.shortcuts import render, get_object_or_404, redirect
from bankaccounts.models import BankAccount, BankAccountType
from .models import DebitTransactions, CreditTransactions
from .forms import DebitTransactionForm, TransferForm
from activity.models import Activity, ActivityType
from django.contrib.auth.decorators import login_required
from datetime import datetime, timezone
from elasticsearch import Elasticsearch
import uuid
from django.conf import settings
from django.core.paginator import Paginator


# Create your views.py here.
@login_required
def transaction_history(request, id):
    # Filter credit and debit transactions for the bank account id
    credit_transactions = CreditTransactions.objects.filter(destination_account=id).order_by('-created_at')
    debit_transactions = DebitTransactions.objects.filter(source_account=id).order_by('-created_at')

    # Combine credit and debit transactions

    transactions = list(credit_transactions) + list(debit_transactions)
    for transaction in transactions:
        if isinstance(transaction, DebitTransactions):
            transaction.value = -abs(transaction.value)

    # Sort transactions by transaction date and time
    transactions.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate transactions with 20 records per page
    paginator = Paginator(transactions, 20)
    page = request.GET.get('page')
    transactions = paginator.get_page(page)

    context = {
        'transactions': transactions,
    }

    return render(request, 'transactions/transactions.html', context)



@login_required
def money_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.user, request.POST)
        if form.is_valid():
            transfer_transaction = form.save(commit=False)
            # update the balance of the source bank account
            source_bank_account = BankAccount.objects.get(id=request.POST.get('source_account'))
            source_bank_account_balance = source_bank_account.balance
            debit_value = float(request.POST.get('value'))
            new_source_bank_account_balance = source_bank_account_balance - debit_value
            source_bank_account.balance = new_source_bank_account_balance
            source_bank_account.save()
            # update the balance of the destination bank account
            destination_bank_account = BankAccount.objects.get(id=request.POST.get('destination_account'))
            destination_bank_account_balance = destination_bank_account.balance
            debit_value = float(request.POST.get('value'))
            new_destination_bank_account_balance = destination_bank_account_balance + debit_value
            destination_bank_account.balance = new_destination_bank_account_balance
            destination_bank_account.save()

            transfer_transaction.save()
            es = Elasticsearch(
                cloud_id=settings.ES_CLOUD_ID,
                http_auth=(settings.ES_USER, settings.ES_PASS)

            )

            record_id = uuid.uuid4()
            document = {
                'id': record_id,
                'timestamp': transfer_transaction.created_at,
                'user.id': source_bank_account.user.id,
                'user.name': source_bank_account.user.username,
                'bank_account': source_bank_account.account_number,
                'full_name': source_bank_account.user.first_name + ' ' + source_bank_account.user.last_name,
                'destination_entity': transfer_transaction.destination_bank,
                'destination_account': transfer_transaction.destination_account,
                'recipient': transfer_transaction.recipient_name,
                'value': transfer_transaction.value,
                'description': transfer_transaction.description,
                'text_field': transfer_transaction.description,
                'reference': transfer_transaction.reference,
                'type': 'Transfer',
                'sub_type': transfer_transaction.transaction_type.name
            }

            es.index(index="transactions", id=record_id, document=document)
            # Redirect to success page
            return redirect('debit-success/{}'.format(request.POST.get('source_account')))
    else:
        form = TransferForm(request.user)
    return render(request, 'transactions/transfer_money.html', {'form': form})


@login_required
def debit_transaction(request):
    if request.method == 'POST':
        form = DebitTransactionForm(request.user, request.POST)
        if form.is_valid():
            debit_transaction = form.save(commit=False)
            bank_account = BankAccount.objects.get(id=request.POST.get('source_account'))
            bank_account_balance = bank_account.balance
            debit_value = float(request.POST.get('value'))
            new_bank_account_balance = bank_account_balance - debit_value
            bank_account.balance = new_bank_account_balance
            bank_account.save()
            debit_transaction.source_account = bank_account
            debit_transaction.save()
            es = Elasticsearch(
                cloud_id=settings.ES_CLOUD_ID,
                http_auth=(settings.ES_USER, settings.ES_PASS)
            )

            record_id = uuid.uuid4()
            document = {
                'id': record_id,
                'timestamp': debit_transaction.created_at,
                'user.id': bank_account.user.id,
                'user.name': bank_account.user.username,
                'bank_account': bank_account.account_number,
                'full_name': bank_account.user.first_name + ' ' + bank_account.user.last_name,
                'destination_entity': debit_transaction.destination_bank,
                'destination_account': debit_transaction.destination_account,
                'recipient': debit_transaction.recipient_name,
                'value': debit_transaction.value,
                'description': debit_transaction.description,
                'text_field': debit_transaction.description,
                'reference': debit_transaction.reference,
                'type': 'Debit',
                'sub_type': debit_transaction.transaction_type.name
            }

            es.index(index="transactions", id=record_id, document=document)
            activity_log_message = "Viewed: Send money form"
            activity_type = ActivityType.objects.get(id=1)
            activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                                      created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
            activity_entry.save()
            return redirect('debit-success/{}'.format(request.POST.get('source_account')))
        else:
            print(form.errors)
    else:
        form = DebitTransactionForm(request.user)
    return render(request, 'transactions/send_money.html', {'form': form})


@login_required
def debit_success(request, id):
    bank_account = BankAccount.objects.get(id=id)
    bank_account_number = bank_account.account_number
    activity_log_message = "Submitted: Send money from: {}".format(bank_account_number)
    activity_type = ActivityType.objects.get(id=1)
    activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                              created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
    activity_entry.save()
    return render(request, 'transactions/debit-success.html', {'source_account': bank_account_number})


@login_required
def transaction_detail(request, id, value):
    value = float(value)
    if value >= 0:
        transaction_details = CreditTransactions.objects.get(id=id)
        transaction_type = "Credit"
    elif value < 0:
        transaction_details = DebitTransactions.objects.get(id=id)
        transaction_type = "Debit"

    context = {
        'my_transaction_details': transaction_details,
        'transaction_type': transaction_type

    }
    activity_log_message = "Viewed: Transaction details for {}".format(transaction_details.reference)
    activity_type = ActivityType.objects.get(id=1)
    activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                              created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
    activity_entry.save()

    return render(request, 'transactions/transaction-detail.html', context)
