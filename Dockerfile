# Stage 1: Build static frontend assets.
FROM node:24.3-alpine as build

ENV NODE_ENV production

# Install dependencies.
WORKDIR /tmp/frontend-build
COPY package.json .yarnrc.yml yarn.lock tailwind.config.js ./
COPY .yarn ./.yarn
RUN yarn install --immutable

# Build h js/css.
COPY .babelrc gulpfile.js rollup.config.js ./
COPY h/static ./h/static
RUN yarn build

# Stage 2: Build the rest of the app using the build output from Stage 1.
FROM python:3.11.11-alpine3.19
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
COPY requirements/prod.txt ./

# Install build deps, build, and then clean up.
RUN apk add --no-cache --virtual build-deps \
    build-base \
    libffi-dev \
    postgresql-dev \
  && pip install --no-cache-dir -U pip \
  && pip install --no-cache-dir -r prod.txt \
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
