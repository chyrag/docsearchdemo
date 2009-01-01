INGEST := ingest
SEARCH := search

.PHONY: all build test run-ingest up clean

all: build

build: build-ingest build-search

build-ingest:
	docker build -f Dockerfile.ingest -t $(INGEST) .

build-search:
	docker build -f Dockerfile.search -t $(SEARCH) .

run-ingest:
	docker run --rm --network=host --volume $(PWD):$(PWD) \
		--volume /tmp:/tmp --workdir $(PWD) --env DROPBOX_TOKEN $(INGEST)

test: build
	docker-compose up -d

up: build
	docker-compose up -d

clean:
	-docker-compose down -v
	-docker rmi $(INGEST) $(SEARCH)
