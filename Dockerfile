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

# Copy minimal data to allow installation of dependencies.
COPY src/memex/__init__.py ./src/memex/
COPY README.rst setup.* requirements.txt ./

# Install application dependencies.
RUN pip install --no-cache-dir -r requirements.txt

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

# Start the web server by default
USER hypothesis
CMD ["gunicorn", "--paste", "conf/app.ini"]
