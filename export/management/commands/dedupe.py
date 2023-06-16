from elasticsearch import Elasticsearch
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Remove duplicates from an elasticsearch index'

    def add_arguments(self, parser):
        parser.add_argument('index', type=str,
                            help='Indicates which index needs to be deduplicated')
        parser.add_argument('field', type=str,
                            help='Indicates which field is used to identify the duplicate')

    def handle(self, *args, **kwargs):
        # create an Elasticsearch client
        es = Elasticsearch(
            cloud_id=settings.ES_CLOUD_ID,
            http_auth=(settings.ES_USER, settings.ES_PASS),
        )

        # define the index and field to search and dedupe on
        index = kwargs['index']
        reference_field = kwargs['field']

        # define the query to retrieve all documents in the index
        query = {
            "query": {
                "match_all": {}
            }
        }

        # execute the query and retrieve all documents
        response = es.search(index=index, body=query, size=10000)
        documents = response['hits']['hits']

        # create a set to store the references of all documents seen so far
        seen_references = set()

        # create a list to store the IDs of the documents to be deleted
        docs_to_delete = []

        # loop through each document in the index
        for document in documents:
            reference = document['_source'][reference_field]
            # if the reference has been seen before, mark the document for deletion
            if reference in seen_references:
                docs_to_delete.append(document['_id'])
            # if the reference has not been seen before, mark the reference as seen
            else:
                seen_references.add(reference)
        print(docs_to_delete)
        response = input("The documents above will be deleted. Do you want to proceed [yes/no]?")
        if response == "yes":
            # delete the duplicate documents from the index
            for doc_id in docs_to_delete:
                es.delete(index=index, id=doc_id)
        else:
            print("You've chosen to back out of the deduplication operation.")