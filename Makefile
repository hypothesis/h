.PHONY: default
default: help

.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make dev               Run the app in the development server"
	@echo "make shell             Launch a Python shell in the dev environment"
	@echo "make sql               Connect to the dev database with a psql shell"
	@echo "make lint              Run the code linter(s) and print any warnings"
	@echo "make analyze           Slower and more thorough code quality analysis (pylint)"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make codecov           Upload the coverage report to codecov.io"
	@echo "make functests         Run the functional tests"
	@echo "make docs              Build docs website and serve it locally"
	@echo "make checkdocs         Crash if building the docs website fails"
	@echo "make docstrings        View all the docstrings locally as HTML"
	@echo "make checkdocstrings   Crash if building the docstrings fails"
	@echo "make pip-compile       Compile requirements.in to requirements.txt"
	@echo "make docker            Make the app's Docker image"
	@echo "make run-docker        Run the app's Docker image locally. "
	@echo "                       This command exists for conveniently testing "
	@echo "                       the Docker image locally in production mode. "
	@echo "                       It assumes the services are being run using "
	@echo "                       docker-compose in the 'h_default' network."
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"

.PHONY: dev
dev: build/manifest.json
	tox -q -e py27-dev

.PHONY: shell
shell:
	tox -q -e py27-dev -- sh bin/hypothesis --dev shell

.PHONY: sql
sql:
	docker-compose exec postgres psql --pset expanded=auto -U postgres

.PHONY: lint
lint:
	tox -q -e py36-lint

.PHONY: analyze
analyze:
	tox -qq -e py36-analyze

.PHONY: format
format:
	tox -q -e py36-format

PHONY: checkformatting
checkformatting:
	tox -q -e py36-checkformatting

.PHONY: test
test: node_modules/.uptodate
	tox
	$(GULP) test

.PHONY: coverage
coverage:
	tox -q -e py36-coverage

.PHONY: codecov
codecov:
	tox -q -e py36-codecov

.PHONY: functests
functests: build/manifest.json
	tox -q -e py27-functests

.PHONY: docs
docs:
	tox -q -e py36-docs

.PHONY: checkdocs
checkdocs:
	tox -q -e py36-checkdocs

.PHONY: docstrings
docstrings:
	tox -q -e py36-docstrings

.PHONY: checkdocstrings
checkdocstrings:
	tox -q -e py36-checkdocstrings

.PHONY: pip-compile
pip-compile:
	tox -q -e py27-dev -- pip-compile --output-file requirements.txt requirements.in

.PHONY: docker
docker:
	git archive --format=tar.gz HEAD | docker build -t hypothesis/hypothesis:$(DOCKER_TAG) -

.PHONY: run-docker
run-docker:
	# To use the local client with the Docker container, you must run the service,
	# navigate to /admin/oauthclients and register an "authorization_code" OAuth
	# client, then restart the service with the `CLIENT_OAUTH_ID` environment
	# variable set.
	#
	# If you don't intend to use the client with the container, you can skip this.
	docker run \
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
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -f node_modules/.uptodate
	rm -rf build

DOCKER_TAG = dev

GULP := node_modules/.bin/gulp

build/manifest.json: node_modules/.uptodate
	$(GULP) build

node_modules/.uptodate: package.json
	@echo installing javascript dependencies
	@node_modules/.bin/check-dependencies 2>/dev/null || npm install
	@touch $@
