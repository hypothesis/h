FROM gliderlabs/alpine:3.3
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --update \
    ca-certificates \
    libffi \
    libpq \
    python \
    py-pip \
    nodejs \
    git \
  && apk add \
    libffi-dev \
    g++ \
    make \
    postgresql-dev \
    python-dev \
  && pip install --no-cache-dir -U pip \
  && rm -rf /var/cache/apk/*

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis \
  && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Copy packaging
COPY h/__init__.py h/_version.py ./h/
COPY README.rst setup.* requirements.txt ./

# Install application dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY gulpfile.js gunicorn.conf.py package.json ./
COPY conf ./conf/
COPY h ./h/
COPY scripts ./scripts/

# Copy prebuilt node-sass binary
COPY vendor ./vendor/

# Build frontend assets
RUN SASS_BINARY_PATH=$PWD/vendor/node-sass-linux-x64.node npm install --production \
  && SASS_BINARY_PATH=$PWD/vendor/node-sass-linux-x64.node NODE_ENV=production node_modules/.bin/gulp build-app \
  && rm -rf node_modules \
  && npm cache clean

# Expose the default port.
EXPOSE 5000

# Set the Python IO encoding to UTF-8.
ENV PYTHONIOENCODING utf_8

# Start the web server by default
USER hypothesis
CMD ["gunicorn", "--paste", "conf/app.ini"]
