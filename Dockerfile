# Stage 1: Build node portion of the H app.
FROM node:11.13-alpine as build

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

# Stage 2: Build the rest of the app using the build output from Stage 1.
FROM alpine:3.9.2
LABEL maintainer="Hypothes.is Project and contributors"

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

# Copy nginx config
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Copy collectd config
COPY conf/collectd.conf /etc/collectd/collectd.conf
RUN mkdir /etc/collectd/collectd.conf.d \
 && chown hypothesis:hypothesis /etc/collectd/collectd.conf.d

# Copy minimal data to allow installation of dependencies.
COPY requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
    build-base \
    libffi-dev \
    postgresql-dev \
    python-dev \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy frontend assets.
COPY --from=build /build build

# Copy the rest of the application files.
COPY . .

# If we're building from a git clone, ensure that .git is writeable
RUN [ -d .git ] && chown -R hypothesis:hypothesis .git || :

# Expose the default port.
EXPOSE 5000

# Set the application environment
ENV PATH /var/lib/hypothesis/bin:$PATH
ENV PYTHONIOENCODING utf_8
ENV PYTHONPATH /var/lib/hypothesis:$PYTHONPATH

# Start the web server by default
USER hypothesis
CMD ["init-env", "supervisord", "-c" , "conf/supervisord.conf"]
