#!/usr/bin/env python3
""" Script for ingesting the PDF documents from Dropbox account """

import os
import sys
import argparse
import logging
import tempfile
import requests
import dropbox  # pylint: disable=import-error
from elasticsearch import Elasticsearch  # pylint: disable=import-error

TIKA_URL = 'http://localhost:9998/tika'
ES_URL = 'localhost:9200'
ES_INDEX = 'docsearchdemo'


def extract_text(fpath):
    """ Extract text from given path """
    try:
        files = {'document': open(fpath, 'rb')}
        headers = {'Content-type': 'application/octet-stream'}
        response = requests.put(TIKA_URL, files=files, headers=headers)
        if not response:
            logging.error('Status: %d', response.status_code)
            return None
        return response.content
    except Exception as error:  # pylint: disable=broad-except
        logging.error(error)
    return None


def submit_data_to_es(client, doc_path, doc_contents):
    """ Submit data to ES """
    try:
        doc_text = str(doc_contents.decode('utf8'))
        body = {'text': doc_text}
        client.index(index=ES_INDEX, id=doc_path, doc_type='_doc', body=body)
    except Exception as error:  # pylint: disable=broad-except
        logging.error('%s: %s', type(error), error)
        sys.exit(1)


def ingest_documents():
    """ Connect to dropbox """

    token = os.getenv('DROPBOX_TOKEN') or None
    dbx = dropbox.Dropbox(token)
    account = dbx.users_get_current_account()
    logging.debug('%s logged in Dropbox', account.name.display_name)

    es_client = Elasticsearch(hosts=[ES_URL])
    client_info = es_client.info()
    logging.debug('Connecting to elasticsearch %s on %s',
                  client_info['version']['number'],
                  client_info['cluster_name'])
    schema = {"mappings": {"properties": {"text": {"type": "text"}}}}
    if not es_client.indices.exists(ES_INDEX):
        logging.debug('Creating index %s', ES_INDEX)
        es_client.indices.create(index=ES_INDEX, body=schema)

    for entry in dbx.files_list_folder('').entries:
        try:
            if os.path.splitext(entry.name)[1] != '.pdf':
                continue
            temp = tempfile.NamedTemporaryFile()
            logging.info('Downloading %s to %s', entry.name, temp.name)
            dbx.files_download_to_file(temp.name, entry.id)

            text = extract_text(temp.name)
            if not text:
                logging.error('Failed to extract text from %s', entry.name)
                continue
            logging.debug('%s [%s...]', entry.name, text[:64])
            with open('{}.txt'.format(temp.name), 'wb') as _fp:
                _fp.write(text)
                _fp.close()
            submit_data_to_es(es_client, entry.name, text)
            temp.close()
        except Exception as error:  # pylint: disable=broad-except
            logging.error(error)
            return 1
    count = es_client.count(index=ES_INDEX)
    logging.info('Total %d documents in ES index', count['count'])
    return 0


def main():
    """ Main routine """
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    log_level = logging.ERROR
    if args.debug:
        log_level = logging.DEBUG
    if args.verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s %(message)s')

    try:
        ingest_documents()
    except Exception as error:  # pylint: disable=broad-except
        logging.error(error)

    es_client = Elasticsearch(hosts=[ES_URL])
    query_body = {"query": {"match": {"text": "chirag"}}}
    results = es_client.search(index=ES_INDEX, body=query_body)
    logging.info('Results: %d', results['hits']['total']['value'])
    for hit in results['hits']['hits']:
        print(hit['_id'])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
