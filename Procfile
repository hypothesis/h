web: gunicorn -w ${WEB_CONCURRENCY:-1} --paster conf/app.ini
notification: hypothesis-worker conf/app.ini notification
nipsa: hypothesis-worker conf/app.ini nipsa
assets: hypothesis assets conf/app.ini
initdb: hypothesis initdb conf/app.ini
