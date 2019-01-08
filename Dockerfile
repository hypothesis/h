# Stage 1: Build frontend assets (eg. JS, CSS bundles).
FROM node:alpine AS node-build

ENV NODE_ENV production

# Build node dependencies.
COPY package-lock.json ./
COPY package.json ./
RUN npm ci --production

# Build h js/css.
COPY gulpfile.js ./
COPY scripts/gulp ./scripts/gulp
COPY h/static ./h/static
RUN npm run build

# Stage 2: Build and install Python dependencies.
FROM alpine:3.7 AS python-build
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    postgresql-dev \
    python-dev \
    py2-pip

RUN pip install --no-cache-dir -U pip

# Install Python packages into `/python`, so we can easily copy them,
# without unrelated files, into the main Docker image.
#
# nb. supervisor requires `pkg_resources` (from `setuptools`) at runtime.
ENV PATH /python/bin:$PATH
COPY requirements.txt ./
RUN pip install --prefix="/python" --no-cache-dir --ignore-installed \
    -r requirements.txt \
    setuptools \
    supervisor

# Stage 3: Build the main image for the h service.
FROM alpine:3.7
LABEL maintainer="Hypothes.is Project and contributors"

# Install runtime dependencies.
# (nb. `git` is indeed required at runtime).
RUN apk add --no-cache \
    ca-certificates \
    collectd \
    collectd-disk \
    collectd-nginx \
    libffi \
    libpq \
    nginx \
    python2

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /var/log/nginx /var/lib/nginx /var/tmp/nginx

# Copy nginx config
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
 && chown hypothesis:hypothesis /etc/collectd/collectd.conf.d

# Copy frontend assets.
COPY --from=node-build /build build

# Copy Python packages and binaries.
COPY --from=python-build /python/ /usr/

# Copy the rest of the application files.
COPY . .

# Expose the default port.
EXPOSE 5000

# Set the application environment
ENV PATH /var/lib/hypothesis/bin:$PATH
ENV PYTHONIOENCODING utf_8
ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

# Start the web server by default
USER hypothesis
CMD ["init-env", "supervisord", "-c" , "conf/supervisord.conf"]
