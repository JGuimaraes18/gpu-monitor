DOCKER_DIR=docker

start:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml up

stop:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml down
