from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from elasticsearch import Elasticsearch
from django.conf import settings
from django.shortcuts import render
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.paginator import Paginator
import uuid


@login_required
def symantec_search(request):
    transactions = []
    search_history = []
    total_value = 0

    es = Elasticsearch(
        cloud_id=settings.ES_CLOUD_ID,
        http_auth=(settings.ES_USER, settings.ES_PASS)
    )
    # handle the search history lookup
    history_index = 'search_history'
    search_history_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"user.id": request.user.id}}
                ]
            }
        },
        "aggs": {
            "query_strings": {  # Aggregations for query strings
                "terms": {
                    "field": "query_string.keyword",  # Aggregate by query string
                    "size": 5  # Limit the number of categories to 100
                }
            }
        }
    }
    history_fields = ["user_id", "query_string"]
    history = es.search(index=history_index, body=search_history_query, size=10, fields=history_fields)
    for hit in history['hits']['hits']:
        search_history.append(hit['_source'])
    query_agg = history['aggregations']['query_strings']['buckets']

    # handle the actual query
    query_term = request.GET.get('q', '')

    end_date_str = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    start_date_str = request.GET.get('start_date', (timezone.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

    # Apply search query if user has entered one
    filter_body = {
        "bool": {
            "must":[
                {
                    "term": {
                        "user.id": {
                            "value": request.user.id
                        }
                    }
                },
                {"term": {
                    "sub-type": {
                        "value": "Purchase, Debit order, EFT"}
                    }
                }
                ],
            "filter": [
                {"range": {
                    "timestamp": {
                        "gte": start_date,
                        "lte": end_date
                    }
                }}
            ]
        }
    }
    if query_term:
        # commit the query term to the history index
        search_record_id = uuid.uuid4()
        search_history_record = {
            'id': str(search_record_id),
            'user.id': request.user.id,
            'query_string': query_term
        }
        es.create(index=history_index, id=search_record_id, document=search_history_record)

        text_expansion_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {
                            "user.id": {
                                "value": request.user.id
                            }
                        }
                        }
                    ],
                    "should": [
                        {
                            "text_expansion": {
                                "ml.tokens": {
                                    "model_id": settings.VECTOR_MODEL,
                                    "model_text": query_term,
                                    "boost": 2
                                }
                            }
                        },
                        {
                            "match": {
                                "description": {
                                    "query": query_term,
                                    "boost": 4
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_date,
                                    "lte": end_date
                                }
                            }
                        }
                    ]
                }
            }

        }
        fields = ["sor.id", "description", "recipient", "sub_type", "value"]
        response = es.search(index='transactions', body=text_expansion_query, size=100, fields=fields)
        for hit in response['hits']['hits']:
            if hit['_score'] > 5:
                hit_data = hit['_source']
                hit_data['score'] = hit['_score']
                transactions.append(hit_data)
                total_value = total_value + hit_data['value']

    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'query': query_term,
        'default_start_date': start_date.strftime('%Y-%m-%d'),
        'default_end_date': end_date.strftime('%Y-%m-%d'),
        'history': search_history,
        'history_agg': query_agg,
        'total_value': total_value
    }

    return render(request, 'uxtools/search_transactions.html', context)


@login_required
def chat_interface(request):
    iframe_url = "http://localhost:3000"  # Replace with your desired iframe URL

    context = {
        'iframe_url': iframe_url,
    }
    return render(request, 'uxtools/chat.html', context)


@login_required
def transactions_map(request):
    es = Elasticsearch(
        cloud_id=settings.ES_CLOUD_ID,
        http_auth=(settings.ES_USER, settings.ES_PASS)

    )
    if 'timeframe' in request.GET:
        months = request.GET['timeframe']
    else:
        months = 3

    months_int = int(months)

    date_range = {
        "range": {
            "timestamp": {
                "gte": (datetime.now() - timedelta(days=months_int * 30)).strftime("%Y-%m-%d"),
                "lte": datetime.now().strftime("%Y-%m-%d")
            }
        }
    }

    user_id = request.user.id

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"sub_type.keyword": "Purchase"}},
                    {"exists": {"field": "location"}},
                    {"term": {"user.id": user_id}},  # Filter by user_id
                    date_range
                ]
            }
        },
        "aggs": {
            "categories": {  # Aggregations for categories
                "terms": {
                    "field": "category.keyword",  # Aggregate by category
                    "size": 100  # Limit the number of categories to 100
                }
            }
        }
    }

    # Get the results from Elasticsearch
    result = es.search(index='transactions', body=query, size=10000)

    # Get the total number of records
    count = result['hits']['total']['value']

    # Prepare the data for the template
    data = []
    for hit in result['hits']['hits']:
        data.append({
            'lat': hit['_source']['location']['lat'],
            'lon': hit['_source']['location']['lon'],
            'value': hit['_source']['value'],
            'category': hit['_source']['category'],
            'destination_entity': hit['_source']['destination_entity']
        })

    categories = result['aggregations']['categories']['buckets']

    # Render the map view with the transaction data
    return render(request, 'uxtools/transactions_map.html',
                  {'data': data, 'count': count, 'months': months, 'categories': categories,
                   'maps_key': settings.GOOGLE_MAPS_API_KEY})
