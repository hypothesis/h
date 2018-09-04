DOCKER_TAG = dev

GULP := node_modules/.bin/gulp

.PHONY: default
default: test

build/manifest.json: node_modules/.uptodate
	$(GULP) build

## Clean up runtime artifacts (needed after a version update)
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate
	rm -rf build

## Run the development H server locally
.PHONY: dev
dev: build/manifest.json
	tox -e dev

## Build hypothesis/hypothesis docker image
.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/hypothesis:$(DOCKER_TAG) -

# Run docker container.
#
# This command exists for conveniently testing the Docker image locally in
# production mode. It assumes the services are being run using docker-compose
# in the `h_default` network.
.PHONY: run-docker
run-docker:
	docker run \
		--net h_default \
		-e "APP_URL=http://localhost:5000" \
		-e "AUTHORITY=localhost" \
		-e "BROKER_URL=amqp://guest:guest@rabbit:5672//" \
		-e "DATABASE_URL=postgresql://postgres@postgres/postgres" \
		-e "ELASTICSEARCH_URL=http://elasticsearch:9200" \
		-e "NEW_RELIC_APP_NAME=h (dev)" \
		-e "NEW_RELIC_LICENSE_KEY" \
		-e "SECRET_KEY=notasecret" \
		-p 5000:5000 \
		hypothesis/hypothesis:$(DOCKER_TAG)

## Run test suite
.PHONY: test
test: node_modules/.uptodate
	tox
	$(GULP) test

.PHONY: test-py3
test-py3: node_modules/.uptodate
	tox -e py36 -- tests/h/

.PHONY: lint
lint:
	tox -e lint

.PHONY: docs
docs:
	tox -e docs

.PHONY: checkdocs
checkdocs:
	tox -e checkdocs

.PHONY: docstrings
docstrings:
	tox -e docstrings

.PHONY: checkdocstrings
checkdocstrings:
	tox -e checkdocstrings

################################################################################

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@

# Self documenting Makefile
.PHONY: help
help:
	@echo "The following targets are available:"
	@echo " clean      Clean up runtime artifacts (needed after a version update)"
	@echo " dev        Run the development H server locally"
	@echo " docker     Build hypothesis/hypothesis docker image"
	@echo " test       Run the test suite (default)"
