from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from elasticsearch import Elasticsearch
from django.conf import settings
from django.shortcuts import render
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q
from django.conf import settings
from elasticsearch.exceptions import NotFoundError
from datetime import datetime, timedelta

# Views

def uxtools_home(request):
    return render(request, 'uxtools/home.html')


@login_required
def myself_at_a_glance(request):
    return render(request, 'uxtools/myself_at_a_glance.html')


@login_required
def advanced_search(request):
    return render(request, 'uxtools/search.html')


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
                    {"term": {"Sub-type.keyword": "Purchase"}},
                    {"exists": {"field": "location"}},
                    {"term": {"User id": user_id}},  # Filter by user_id
                    date_range
                ]
            }
        },
        "aggs": {
            "categories": {  # Aggregations for categories
                "terms": {
                    "field": "Category.keyword",  # Aggregate by category
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
            'value': hit['_source']['Value'],
            'category': hit['_source']['Category'],
            'destination_entity': hit['_source']['Destination entity']
        })

    categories = result['aggregations']['categories']['buckets']

    # Render the map view with the transaction data
    return render(request, 'uxtools/transactions_map.html', {'data': data, 'count': count, 'months': months, 'categories': categories, 'maps_key': settings.GOOGLE_MAPS_API_KEY})

