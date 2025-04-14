DOCKER_DIR=docker

start:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml up --build

stop:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml down
