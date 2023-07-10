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
	@echo "                       docker compose in the 'h_default' network."

.PHONY: services
services: args?=up -d --wait
services: python
	@docker compose $(args)

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
	@docker compose exec postgres psql --pset expanded=auto -U postgres

.PHONY: lint
lint: frontend-lint backend-lint

.PHONY: backend-lint
backend-lint: python
	@tox -qe lint

.PHONY: frontend-lint
frontend-lint: node_modules/.uptodate
	@yarn lint

.PHONY: format
format: backend-format frontend-format

.PHONY: backend-format
backend-format: python
	@tox -qe format

.PHONY: frontend-format
frontend-format: node_modules/.uptodate
	@yarn format

PHONY: checkformatting
checkformatting: backend-checkformatting frontend-checkformatting

.PHONY: backend-checkformatting
backend-checkformatting: python
	@tox -qe checkformatting

.PHONY: frontend-checkformatting
frontend-checkformatting: node_modules/.uptodate
	@yarn checkformatting

.PHONY: test
test: backend-tests frontend-tests

.PHONY: backend-tests
backend-tests: python
	@tox -q

.PHONY: frontend-tests
frontend-tests: node_modules/.uptodate
	@yarn test

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

# Tell make how to compile requirements/*.txt files.
#
# `touch` is used to pre-create an empty requirements/%.txt file if none
# exists, otherwise tox crashes.
#
# $(subst) is used because in the special case of making requirements.txt we
# actually need to touch dev.txt not requirements.txt and we need to run
# `tox -e dev ...` not `tox -e requirements ...`
#
# $(basename $(notdir $@))) gets just the environment name from the
# requirements/%.txt filename, for example requirements/foo.txt -> foo.
requirements/%.txt: requirements/%.in
	@touch -a $(subst requirements.txt,dev.txt,$@)
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip --quiet --disable-pip-version-check install pip-tools'
	@tox -qe $(subst requirements,dev,$(basename $(notdir $@))) --run-command 'pip-compile --no-allow-unsafe --quiet $(args) $<'

# Inform make of the dependencies between our requirements files so that it
# knows what order to re-compile them in and knows to re-compile a file if a
# file that it depends on has been changed.
requirements/dev.txt: requirements/requirements.txt
requirements/tests.txt: requirements/requirements.txt
requirements/functests.txt: requirements/requirements.txt
requirements/lint.txt: requirements/tests.txt requirements/functests.txt

# Add a requirements target so you can just run `make requirements` to
# re-compile *all* the requirements files at once.
#
# This needs to be able to re-create requirements/*.txt files that don't exist
# yet or that have been deleted so it can't just depend on all the
# requirements/*.txt files that exist on disk $(wildcard requirements/*.txt).
#
# Instead we generate the list of requirements/*.txt files by getting all the
# requirements/*.in files from disk ($(wildcard requirements/*.in)) and replace
# the .in's with .txt's.
.PHONY: requirements requirements/
requirements requirements/: $(foreach file,$(wildcard requirements/*.in),$(basename $(file)).txt)

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
		--rm \
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
		-e "ENABLE_NGINX=true" \
		-e "ENABLE_WEB=true" \
		-e "ENABLE_WEBSOCKET=true" \
		-e "WEBSOCKET_CONFIG=conf/websocket-monolithic.ini" \
		-e "ENABLE_WORKER=true" \
		-p 5000:5000 \
		--name hypothesis \
		hypothesis/hypothesis:$(DOCKER_TAG)

DOCKER_TAG = dev

build/manifest.json: node_modules/.uptodate
	@yarn build

node_modules/.uptodate: package.json yarn.lock
	@echo installing javascript dependencies
	@yarn install
	@touch $@

.PHONY: python
python:
	@./bin/install-python
