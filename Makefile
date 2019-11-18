# Image URL to use all building/pushing image targets
REGISTRY ?= quay.io
REPOSITORY ?= $(REGISTRY)/eformat/controlm

IMG := $(REPOSITORY):latest

# Docker Login
docker-login:
	@docker login -u $(DOCKER_USER) -p $(DOCKER_PASSWORD) $(REGISTRY)

# Build the docker image
docker-build:
	docker build . -t ${IMG} --build-arg CTMHOST=localhost --build-arg CTMENV=workbench -f Dockerfile

# Push the docker image
docker-push: docker-build
	docker push ${IMG}
