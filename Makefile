NAME := ingest

.PHONY: all build test clean

all: build

build:
	docker build -t $(NAME) .

test: build
	docker run --rm --network=host --volume $(PWD):$(PWD) \
		--volume /tmp:/tmp --workdir $(PWD) --env DROPBOX_TOKEN $(NAME)

clean:
	-docker rmi $(NAME)
