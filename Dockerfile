# Stage 1: Build static frontend assets.
FROM node:19-alpine as build

ENV NODE_ENV production

# Install dependencies.
WORKDIR /tmp/frontend-build
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Build h js/css.
COPY .babelrc gulpfile.mjs rollup.config.mjs ./
COPY h/static ./h/static
RUN yarn build

# Stage 2: Build the rest of the app using the build output from Stage 1.
FROM python:3.8.12-alpine3.13
LABEL maintainer="Hypothes.is Project and contributors"

# Install system build and runtime dependencies.
RUN apk add --no-cache \
    libffi \
    libpq \
    nginx \
    git

# Create the hypothesis user, group, home directory and package directory.
RUN addgroup -S hypothesis && adduser -S -G hypothesis -h /var/lib/hypothesis hypothesis
WORKDIR /var/lib/hypothesis

# Ensure nginx state and log directories writeable by unprivileged user.
RUN chown -R hypothesis:hypothesis /var/log/nginx /var/lib/nginx

# Copy nginx config
COPY conf/nginx.conf /etc/nginx/nginx.conf

# Copy minimal data to allow installation of dependencies.
COPY requirements/requirements.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
    build-base \
    libffi-dev \
    postgresql-dev \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-deps

# Copy frontend assets.
COPY --from=build /tmp/frontend-build/build build

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
