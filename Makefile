IMAGE_NAME ?= tch
CONTAINER_NAME ?= TCH
VOLUME ?= $(PWD):/TCH/VOLUME
VERSION = $(shell python3 run.py --version | grep -o -E v.+)

DOCKER = docker
DANGLING_IMAGE = $(shell $(DOCKER) images -f dangling=true -q)
LATEST_TCH_IMAGE = $(shell $(DOCKER) images --filter=reference="tch" -q)

.PHONY: buld version test clean

build:
ifneq ($(LATEST_TCH_IMAGE),)
	$(DOCKER) rmi -f $(LATEST_TCH_IMAGE)
endif

	$(DOCKER) build -t $(IMAGE_NAME):$(VERSION) ./
	$(DOCKER) tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

ifneq ($(DANGLING_IMAGE),)
	$(DOCKER) rmi $(DANGLING_IMAGE)
endif

test:
	$(DOCKER) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) -l full -c VOLUME/Examples/SortTheList/

run:
	$(DOCKER) run --name $(CONTAINER_NAME) -v $(VOLUME) -it --rm $(IMAGE_NAME):$(VERSION) $(ARGS)

version:
	@echo $(VERSION)

clean:
ifneq ($(LATEST_TCH_IMAGE),)
	$(DOCKER) rmi -f $(LATEST_TCH_IMAGE)
endif

ifneq ($(DANGLING_IMAGE),)
	$(DOCKER) rmi $(DANGLING_IMAGE)
endif