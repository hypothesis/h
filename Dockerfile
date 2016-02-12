FROM gliderlabs/alpine:3.2
MAINTAINER Hypothes.is Project and contributors

# Install system build and runtime dependencies.
RUN apk add --update \
    ca-certificates \
    libffi \
    libpq \
    python \
    py-pip \
    nodejs \
    ruby \
  && apk add \
    libffi-dev \
    g++ \
    make \
    postgresql-dev \
    python-dev \
    ruby-dev \
  && gem install --no-ri compass \
  && pip install --no-cache-dir -U pip \
  && rm -rf /var/cache/apk/*

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis \
  && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Copy packaging
COPY h/__init__.py h/_version.py ./h/
COPY README.rst package.json setup.* requirements.txt ./

# Install application dependencies.
RUN npm install --production \
  && pip install --no-cache-dir -r requirements.txt \
  && npm cache clean

# Copy the rest of the application files
COPY gunicorn.conf.py ./
COPY conf ./conf/
COPY h ./h/
COPY scripts ./scripts/

# Expose the default port.
EXPOSE 5000

# Set the Python IO encoding to UTF-8.
ENV PYTHONIOENCODING utf_8

# Build the assets
RUN hypothesis assets conf/app.ini

# Allow the application to modify the webassets directory
RUN chown -R hypothesis:hypothesis h/static/

# Persist the static directory.
VOLUME ["/var/lib/hypothesis/h/static"]

# Start the web server by default
USER hypothesis
CMD ["gunicorn", "--paste", "conf/app.ini"]
