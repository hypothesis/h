.PHONY: frontend-format
$(call help,make frontend-format,"format the frontend code")
frontend-format: node_modules/.uptodate
	@yarn format

.PHONY: frontend-checkformatting
$(call help,make frontend-checkformatting,"crash if the frontend code isn't correctly formatted")
frontend-checkformatting: node_modules/.uptodate
	@yarn checkformatting

.PHONY: frontend-lint
$(call help,make frontend-lint,"lint the frontend code")
frontend-lint: node_modules/.uptodate
	@yarn lint

.PHONY: frontend-tests
$(call help,make frontend-tests,"run the frontend tests")
frontend-tests: node_modules/.uptodate
	@yarn test

build/manifest.json: node_modules/.uptodate
	@yarn build

node_modules/.uptodate: package.json yarn.lock
	@echo installing javascript dependencies
	@yarn install
	@touch $@

dev: build/manifest.json
devssl: build/manifest.json
functests: build/manifest.json
sure: build/manifest.json

sure: frontend-checkformatting frontend-lint frontend-tests
