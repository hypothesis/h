web: gunicorn -w ${WEB_CONCURRENCY:-1} --paster conf/${HYP_ENV:-production}.ini
notification: hypothesis-worker conf/${HYP_ENV:-production}.ini notification
nipsa: hypothesis-worker conf/${HYP_ENV:-production}.ini nipsa
assets: hypothesis assets conf/${HYP_ENV:-production}.ini
initdb: hypothesis initdb conf/${HYP_ENV:-production}.ini
