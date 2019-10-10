.PHONY: help
help:
	@echo "make help              Show this help message"
	@echo "make lint              Code quality analysis (pylint)"
	@echo "make format            Correctly format the code"
	@echo "make checkformatting   Crash if the code isn't correctly formatted"

	@echo "make package           Create package in the dist/ directory"
	@echo "make publish           Publish packages created in the dist/ directory"
	@echo "make test              Run the unit tests"
	@echo "make coverage          Print the unit test coverage report"
	@echo "make codecov           Upload the coverage report to codecov.io"
	@echo "make pip-compile       Compile requirements.in to requirements.txt."
	@echo "                       Use this command after editing requirements.in, for"
	@echo "                       example after adding or removing a requirement."
	@echo "make upgrade-package   Upgrade the version of a package in requirements.txt."
	@echo '                       Usage: `make upgrade-package name=some-package`.'
	@echo "make clean             Delete development artefacts (cached files, "
	@echo "                       dependencies, etc)"


.PHONY: lint
lint: python
	tox -qq -e py36-lint

.PHONY: format
format: python
	tox -q -e py36-format

.PHONY: checkformatting
checkformatting: python
	tox -q -e py36-checkformatting

.PHONY: package
package: python
	tox -q -e py36-package

.PHONY: publish
publish: python
	tox -q -e py36-publish

.PHONY: test
test: python
	tox

.PHONY: coverage
coverage: python
	tox -q -e py36-coverage

.PHONY: codecov
codecov: python
	tox -q -e py36-codecov

.PHONY: pip-compile
pip-compile: python
	tox -q -e py36-pip-compile

.PHONY: upgrade-package
upgrade-package: python
	@tox -qe py36-dev -- pip-compile --upgrade-package $(name)

.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build .eggs dist *.egg-info

.PHONY: python
python:
	@./bin/install-python
