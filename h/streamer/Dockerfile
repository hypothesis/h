ARG DOCKER_TAG=latest
FROM hypothesis/hypothesis:${DOCKER_TAG}

WORKDIR /var/lib/hypothesis

COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/supervisord.conf conf/supervisord.conf

# Start the web server by default
USER hypothesis
CMD ["init-env", "supervisord", "-c" , "conf/supervisord.conf"]
