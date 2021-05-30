#!/usr/bin/env python3
""" Flask based search service """

import json
import logging
from flask import Flask, request  # pylint: disable=import-error
from elasticsearch import Elasticsearch  # pylint: disable=import-error

ES_HOST = 'localhost:9200'
ES_INDEX = 'docsearchdemo'

app = Flask(__name__)
es_client = Elasticsearch(hosts=[ES_HOST])


@app.route('/')
def index():
    """ Index routine """
    return json.dumps({})


@app.route('/search')
def search():
    """ Search routine """
    search_term = request.args.get('q')
    query_body = {"query": {"match": {"text": search_term}}}
    es_response = es_client.search(index=ES_INDEX, body=query_body)
    try:
        count = es_response['hits']['total']['value']
        hits = [hit['_id'] for hit in es_response['hits']['hits']]
        response = {'items': count, 'paths': hits}
        return response
    except Exception as error:  # pylint: disable=broad-except
        logging.warning('%s: %s', type(error), error)
    return es_response


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
app.run(host='0.0.0.0', port=9000)
