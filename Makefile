# https://lithic.tech/blog/2020-05/makefile-dot-env
include .env.example
export
DOCKER_ENV_FILE_PARAM = --env-file .env.example
ifneq (,$(wildcard ./.env))
	include .env
	export
	DOCKER_ENV_FILE_PARAM = --env-file .env.example --env-file .env
endif

DOCKER ?= docker
export PROJECT_NAME ?= slack_zendesk_integration
PROJECT_DOCKER_COMPOSE = $(DOCKER) compose --project-name $(PROJECT_NAME) --file ./docker-compose.yaml --project-directory . $(DOCKER_ENV_FILE_PARAM)



HERE = $(shell pwd)
DOCKER_IMAGE_LOCAL_PROD ?= slack-zendesk-int:latest
DOCKER_IMAGE_LOCAL_DEV ?= slack-zendesk-int-local-dev:latest
GIT_HASH ?= $(shell git rev-parse HEAD)
# change the below
DOCKER_IMAGE_GCP ?= {docker image name}:$(GIT_HASH)
GCP_PROJECT ?= {project name}
GCP_RUN_APPNAME ?= {app name}
GCP_RUN_REGION ?= {region}
GCP_RUN_SERVICE_ACCOUNT ?= {service account}
GCP_SQL_INSTANCE ?= {SQL instance}
GCP_SQL_INSTANCE_USER ?= postgres
GCP_SQL_INSTANCE_DATABASE ?= state

.PHONY: build
build:
	$(DOCKER) build \
		--platform=linux/amd64 \
		--tag $(DOCKER_IMAGE_LOCAL_PROD) \
		--tag $(DOCKER_IMAGE_GCP) \
		.

.PHONY: run
run: build
	$(DOCKER) run \
		--rm \
		--tty \
		--interactive \
		$(DOCKER_ENV_FILE_PARAM) \
		--publish $(PORT):$(PORT) \
		$(DOCKER_IMAGE_LOCAL_PROD)

		# --detach \


.PHONY: docker-push
docker-push: build
	$(DOCKER) push $(DOCKER_IMAGE_GCP)

.PHONY: gcp-deploy
gcp-deploy: docker-push
	gcloud run deploy \
		--project=$(GCP_PROJECT) \
		--region=$(GCP_RUN_REGION) \
		--image=$(DOCKER_IMAGE_GCP) \
		--platform=managed \
		--ingress=all \
		--allow-unauthenticated \
		--timeout=30 \
		--min-instances=1 \
		--max-instances=1 \
		--cpu=1 \
		--memory=512Mi \
		--execution-environment=gen1 \
		--set-cloudsql-instances=$(GCP_SQL_INSTANCE) \
		--set-secrets=SLACK_CLIENT_ID={client id}:latest,SLACK_CLIENT_SECRET={client secret}:latest,SLACK_SIGNING_SECRET={signing secret}:latest,POSTGRES_PASSWORD={postgres password}:latest \
		--set-env-vars=POSTGRES_HOST=/cloudsql/$(GCP_SQL_INSTANCE),POSTGRES_PORT=5432,POSTGRES_USER=$(GCP_SQL_INSTANCE_USER),POSTGRES_DATABASE=$(GCP_SQL_INSTANCE_DATABASE) \
		--service-account=$(GCP_RUN_SERVICE_ACCOUNT) \
		--description="{description}" \
		$(GCP_RUN_APPNAME)

.PHONY: build-dev
build-dev:
	$(DOCKER) build \
		--file dev.dockerfile \
		--tag $(DOCKER_IMAGE_LOCAL_DEV) \
		.

.PHONY: run-dev
run-dev: build-dev
	$(DOCKER) run \
		--rm \
		--tty \
		--interactive \
		$(DOCKER_ENV_FILE_PARAM) \
		--volume $(HERE)/app.py:/work/app.py \
		--volume $(HERE)/config.py:/work/config.py \
		--volume $(HERE)/dbshell.sh:/work/dbshell.sh \
		--volume $(HERE)/requirements.txt:/work/requirements.txt \
		--volume $(HERE)/run.sh:/work/run.sh \
		--publish $(PORT):$(PORT) \
		$(DOCKER_IMAGE_LOCAL_DEV)

.PHONY: up
up:
	$(PROJECT_DOCKER_COMPOSE) up --detach --force-recreate

.PHONY: down
down:
	$(PROJECT_DOCKER_COMPOSE) down

.PHONY: clean
clean:
	-$(PROJECT_DOCKER_COMPOSE) rm
	-$(DOCKER) container rm \
		$(PROJECT_NAME)_app \
		$(PROJECT_NAME)_db
	-$(DOCKER) image rm \
		$(PROJECT_NAME)_app

.PHONY: dbdel
dbdel:
	-$(DOCKER) volume rm \
		$(PROJECT_NAME)_pgdata

.PHONY: logs
logs:
	$(PROJECT_DOCKER_COMPOSE) logs --follow

.PHONY: login
login:
	$(DOCKER) exec -ti $(PROJECT_NAME)_app bash

.PHONY: stop
stop:
	$(MAKE) down
	$(MAKE) clean

.PHONY: start
start:
	$(MAKE) up
	# $(MAKE) logs
	$(MAKE) login

.PHONY: restart
restart:
	$(MAKE) stop
	$(MAKE) start
 
