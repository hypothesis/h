.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo 'make services          Run the services that `make dev` requires'
	@echo "                       (Postgres, Elasticsearch, etc) in Docker Compose"
	@echo 'make db                Upgrade the DB schema to the latest version'
	@echo "make dev               Run the app in the development server"
	@echo "make devdata           Upsert standard development data into the DB, and set"
	@echo "                       standard environment variables for a development"
	@echo "                       environment"
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make analyze           Slower and more thorough code quality analysis (pylint)"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make backend-tests     Run the backend unit tests"
	@echo "make frontend-tests    Run the frontend unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make functests         Run the functional tests"
	@echo "make docs              Build docs website and serve it locally"
	@echo "make checkdocs         Crash if building the docs website fails"
	@echo "make sure              Make sure that the formatter, linter, tests, etc all pass"
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally. "
	@echo "                       This command exists for conveniently testing "
	@echo "                       the Docker image locally in production mode. "
	@echo "                       It assumes the services are being run using "
	@echo "                       docker-compose in the 'h_default' network."
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: services
services: args?=up -d
services: python
	@tox -qe dockercompose -- $(args)

.PHONY: db
db: args?=upgrade head
db: python
	@tox -qqe dev --run-command 'sh bin/hypothesis --dev init'
	@tox -qe dev --run-command 'sh bin/hypothesis --dev migrate $(args)'

.PHONY: dev
dev: build/manifest.json python
	@tox -qe dev

.PHONY: devssl
devssl: export H_GUNICORN_CERTFILE=.tlscert.pem
devssl: export H_GUNICORN_KEYFILE=.tlskey.pem
devssl: export APP_URL=https://localhost:5000
devssl: export WEBSOCKET_URL=wss://localhost:5001/ws
devssl: build/manifest.json python
	@tox -qe dev

.PHONY: devdata
devdata: python
	@tox -qe dev -- sh bin/hypothesis --dev devdata

.PHONY: shell
shell: python
	@tox -qe dev -- sh bin/hypothesis --dev shell

.PHONY: sql
sql: python
	@tox -qe dockercompose -- exec postgres psql --pset expanded=auto -U postgres

.PHONY: lint
lint: backend-lint frontend-lint

.PHONY: backend-lint
backend-lint: python
	@tox -qe lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	@npm lint

.PHONY: analyze
analyze: python
	@tox -qe analyze

.PHONY: format
format: python
	@tox -qe format

PHONY: checkformatting
checkformatting: backend-checkformatting frontend-checkformatting

.PHONY: backend-checkformatting
backend-checkformatting: python
	@tox -qe checkformatting

.PHONY: frontend-checkformatting
frontend-checkformatting: node_modules/.uptodate
	@npm checkformatting

.PHONY: test
test: backend-tests frontend-tests

.PHONY: backend-tests
backend-tests: python
	@tox -q

.PHONY: frontend-tests
frontend-tests: node_modules/.uptodate
	@npm test

.PHONY: coverage
coverage: python
	@tox -qe coverage

.PHONY: functests
functests: build/manifest.json python
	@tox -qe functests

.PHONY: docs
docs: python
	@tox -qe docs

.PHONY: checkdocs
checkdocs: python
	@tox -qe checkdocs

.PHONY: sure
sure: checkformatting lint test coverage functests

.PHONY: docker
docker:
	@git archive --format=tar.gz HEAD | docker build -t hypothesis/hypothesis:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	# To use the local client with the Docker container, you must run the service,
	# navigate to /admin/oauthclients and register an "authorization_code" OAuth
	# client, then restart the service with the `CLIENT_OAUTH_ID` environment
	# variable set.
	#
	# If you don't intend to use the client with the container, you can skip this.
	@docker run \
		--net h_default \
		-e "APP_URL=http://localhost:5000" \
		-e "AUTHORITY=localhost" \
		-e "BROKER_URL=amqp://guest:guest@rabbit:5672//" \
		-e "CLIENT_OAUTH_ID" \
		-e "CLIENT_URL=http://localhost:3001/hypothesis" \
		-e "DATABASE_URL=postgresql://postgres@postgres/postgres" \
		-e "ELASTICSEARCH_URL=http://elasticsearch:9200" \
		-e "NEW_RELIC_APP_NAME=h (dev)" \
		-e "NEW_RELIC_LICENSE_KEY" \
		-e "SECRET_KEY=notasecret" \
		-p 5000:5000 \
		hypothesis/hypothesis:$(DOCKER_TAG)

.PHONY: clean
clean:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -f node_modules/.uptodate
	@rm -rf build

DOCKER_TAG = dev

build/manifest.json: node_modules/.uptodate
	@npm build

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@

.PHONY: python
python:
	@./bin/install-python
