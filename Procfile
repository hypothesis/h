web: ./bin/heroku-shim newrelic-admin run-program gunicorn --bind "0.0.0.0:${PORT}" --paste conf/app.ini
release: ./bin/heroku-shim ./bin/hypothesis --app-url http://localhost:5000 init
worker: ./bin/heroku-shim ./bin/hypothesis celery worker -l INFO
beat: ./bin/heroku-shim ./bin/hypothesis celery beat
