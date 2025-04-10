DOCKER_DIR=docker

# Alvo para subir os containers
start:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml up -d

# Alvo para derrubar os containers
stop:
	docker-compose -f $(DOCKER_DIR)/docker-compose.yml down
