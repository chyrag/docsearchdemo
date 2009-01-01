FROM python:3-alpine

RUN pip3 install dropbox==11.10.0 elasticsearch==7.13.0

COPY ingest.py /ingest

ENTRYPOINT ["/ingest"]
