FROM node:alpine as build

ENV NODE_ENV production

COPY . .

RUN npm install --production && npm run build

FROM alpine:3.7
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --no-cache \
    ca-certificates \
    collectd \
    collectd-disk \
    collectd-nginx \
    libffi \
    libpq \
    nginx \
    python2 \
    py2-pip \
    git

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /var/log/nginx /var/lib/nginx /var/tmp/nginx

# Copy minimal data to allow installation of dependencies.
COPY requirements.txt ./

# BEGIN WORKAROUND
#
# TODO: Remove this workaround once https://github.com/pyca/cryptography/issues/4264 is resolved.
#
# crypotography (one of the dependencies that would be installed from our
# requirements.txt file below) currently has a problem building against
# LibreSSL (LibreSSL is going to be installed as a dependency of some of the
# apk packages installed below):
#
# https://github.com/pyca/cryptography/issues/4264
#
# So as a workaround install cryptography separately now, before LibreSSL gets
# installed.
RUN apk update                                  # Needed or `apk add openssl-dev` won't work.
RUN apk add openssl-dev                         # Build cryptography against OpenSSL, which works,
                                                # instead of against LibreSSL.
RUN apk add gcc python-dev musl-dev libffi-dev  # Other dependencies needed to build cryptography.
RUN pip install --no-cache-dir -U pip
RUN pip install cryptography==2.1.4
# Remove OpenSSL again because it conflicts with LibreSSL which is going to be installed as a
# dependency of some of the apk packages below.
RUN apk del openssl-dev
# END WORKAROUND

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
    build-base \
    libffi-dev \
    postgresql-dev \
    python-dev \
  && pip install --no-cache-dir -U pip supervisor \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy nginx config
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
 && chown hypothesis:hypothesis /etc/collectd/collectd.conf.d

# Copy the rest of the application files.
COPY . .

# If we're building from a git clone, ensure that .git is writeable
RUN [ -d .git ] && chown -R hypothesis:hypothesis .git || :

# Copy frontend assets.
COPY --from=build /build build

# Expose the default port.
EXPOSE 5000

# Set the application environment
ENV PATH /var/lib/hypothesis/bin:$PATH
ENV PYTHONIOENCODING utf_8
ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

# Start the web server by default
USER hypothesis
CMD ["init-env", "supervisord", "-c" , "conf/supervisord.conf"]
