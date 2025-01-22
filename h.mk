.PHONY: docs

$(call help,make docs,"build the docs website and serve it locally")
docs: python
	@tox -qe docs

.PHONY: checkdocs
$(call help,make checkdocs,"crash if building the docs website fails")
checkdocs: python
	@tox -qe checkdocs

.PHONY: devssl
devssl: export GUNICORN_CERTFILE=.tlscert.pem
devssl: export GUNICORN_KEYFILE=.tlskey.pem
devssl: export APP_URL=https://localhost:5000
devssl: export WEBSOCKET_URL=wss://localhost:5001/ws
devssl: build/manifest.json python
	@tox -qe dev
