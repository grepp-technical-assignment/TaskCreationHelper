IMAGE_NAME ?= tch
CONTAINER_NAME ?= TCH
VOLUME ?= $(PWD):/TCH/VOLUME

CAT := $(if $(filter $(OS),Windows_NT),type,cat)
DOCKER = docker

VERSION = $(shell $(CAT) $(PWD)/VERSION)


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