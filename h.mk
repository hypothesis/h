db:
	@tox -qqe dev --run-command 'sh bin/hypothesis --dev init'
	@tox -qe dev --run-command 'sh bin/hypothesis --dev migrate $(args)'

shell:
	@tox -qe dev -- sh bin/hypothesis --dev shell
