IMAGE_NAME ?= tch
CONTAINER_NAME ?= TCH
VOLUME ?= $(PWD):/TCH/VOLUME
VERSION = $(shell python3 run.py --version | grep -o -E v.+)

CC = docker

.PHONY: buld version test

build:
	$(CC) build -t $(IMAGE_NAME):$(VERSION) ./

test:
	$(CC) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) -l full -c VOLUME/Examples/SortTheList/

run:
	$(CC) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) $(ARGS)

version:
	@echo $(VERSION)