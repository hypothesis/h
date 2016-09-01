FROM gliderlabs/alpine:3.4
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk-install \
    ca-certificates \
    libffi \
    libpq \
    python \
    py-pip \
    nodejs \
    git

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Copy minimal data to allow installation of dependencies.
COPY src/memex/__init__.py ./src/memex/
COPY README.rst setup.* requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk-install --virtual build-deps \
    build-base \
    libffi-dev \
    postgresql-dev \
    python-dev \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy the rest of the application files.
COPY . .

# Build frontend assets
RUN SASS_BINARY_PATH=$PWD/vendor/node-sass-linux-x64.node npm install --production \
  && SASS_BINARY_PATH=$PWD/vendor/node-sass-linux-x64.node NODE_ENV=production node_modules/.bin/gulp build \
  && (find node_modules -name hypothesis -prune -o -mindepth 1 -maxdepth 1 -print0 | xargs -0 rm -r) \
  && npm cache clean

# Expose the default port.
EXPOSE 5000

# Set the application environment
ENV PATH /var/lib/hypothesis/bin:$PATH
ENV PYTHONIOENCODING utf_8
ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

# Start the web server by default
USER hypothesis
CMD ["newrelic-admin", "run-program", "gunicorn", "--paste", "conf/app.ini"]
