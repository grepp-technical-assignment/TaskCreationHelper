IMAGE_NAME ?= tch
CONTAINER_NAME ?= TCH

DOCKER = docker

ifeq ($(OS),Windows_NT)
    VERSION := $(shell type VERSION)
	VOLUME ?= $(CURDIR):/TCH/VOLUME
else
    VERSION = $(shell cat $(PWD)/VERSION)
	VOLUME ?= $(PWD):/TCH/VOLUME
endif

DANGLING_IMAGE = $(shell $(DOCKER) images -f dangling=true -q)
LATEST_TCH_IMAGE = $(shell $(DOCKER) images --filter=reference="tch" -q)

build:
ifneq ($(LATEST_TCH_IMAGE),)
	@$(DOCKER) rmi -f $(LATEST_TCH_IMAGE)
endif

	@$(DOCKER) build -t $(IMAGE_NAME):$(VERSION) ./
	@$(DOCKER) tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

ifneq ($(DANGLING_IMAGE),)
	@$(DOCKER) rmi $(DANGLING_IMAGE)
endif
.PHONY: build

test:
	@$(DOCKER) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) -l full -c VOLUME/Examples/SortTheList/
.PHONY: test

run:
	@$(DOCKER) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) $(ARGS)
.PHONY: run

version:
	@echo $(VERSION)
.PHONY: version

clean:
ifneq ($(LATEST_TCH_IMAGE),)
	@$(DOCKER) rmi -f $(LATEST_TCH_IMAGE)
endif

ifneq ($(DANGLING_IMAGE),)
	@$(DOCKER) rmi $(DANGLING_IMAGE)
endif
.PHONY: clean