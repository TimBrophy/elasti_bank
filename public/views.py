from django.shortcuts import render
from activity.models import Activity, ActivityType
from bankaccounts.models import BankAccount, BankAccountType
from transactions.models import CreditTransactions, DebitTransactions
from uxtools.models import SpecialOffer
from .forms import ContactForm
from datetime import datetime, timezone, timedelta
from elasticsearch import Elasticsearch
from django.conf import settings


def check_campaign_exists(offer_transactions, campaign_name):
    for transaction in offer_transactions:
        if transaction.get('campaign_name') == campaign_name:
            return True
    return False

# Create your views.py here.


def home(request):
    form = ContactForm()
    net_worth = 0
    my_accounts = []
    most_recent_transactions = []
    offer_list = []
    offer_transactions = []
    offer_dict = {}
    if request.user.is_authenticated:
        # run a search using Special Offers to see if the customer is eligible for any of them
        current_special_offers = SpecialOffer.objects.all()

        es = Elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            http_auth=(settings.ES_USER, settings.ES_PASS)
        )

        offer_list = []
        offer_transactions = []
        offer_dict = {}
        # filter_body = {
        #     "bool": {
        #         "must":
        #             {
        #                 "term": {
        #                     "user_id": {
        #                         "value": request.user.id
        #                     }
        #                 }
        #             }
        #     }
        # }

        for i in current_special_offers:
            vector_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {
                                "user.id": {
                                    "value": request.user.id
                                }
                            }
                            },
                            {
                                "text_expansion": {
                                    "ml.tokens": {
                                        "model_id": settings.VECTOR_MODEL,
                                        "model_text": i.description
                                    }
                                }
                            }
                        ]
                    }
                }

            }
            # vector_query = {
            #     "knn": {
            #         "field": "dense-vector-field",
            #         "k": 10,
            #         "num_candidates": 100,
            #         "query_vector_builder": {
            #             "text_embedding": {
            #                 "model_id": settings.VECTOR_MODEL,
            #                 "model_text": i.description
            #             }
            #         }
            #     }
            # }

            fields = ["sor.id", "description", "recipient", "sub_type", "value"]
            response = es.search(index='transactions', body=vector_query, size=5, fields=fields)

            for hit in response['hits']['hits']:
                if hit['_score'] > 5:
                    hit_data = hit['_source']
                    hit_data['campaign_name'] = i.name
                    hit_data['score'] = hit['_score']
                    offer_transactions.append(hit_data)

            # check whether there are any current active campaigns
            campaign_exists = check_campaign_exists(offer_transactions, i.name)
            if campaign_exists:
                offer_dict = {'name': i.name, 'description': i.description}
                offer_list.append(offer_dict)

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

        most_recent_transactions = transactions[:5]

        activity_log_message = "Viewed: home page"
        activity_type = ActivityType.objects.get(id=1)
        activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                                  created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
        activity_entry.save()

    bankaccounttypes = BankAccountType.objects.all()

    return render(request, 'home.html', {'form': form, 'net_worth': net_worth,
                                         'bankaccounttypes_list': bankaccounttypes, 'my_accounts': my_accounts,
                                         'transactions': most_recent_transactions,
                                         'offer_transactions': offer_transactions,
                                         'offers': offer_list})
