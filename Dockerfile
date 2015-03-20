FROM phusion/baseimage:0.9.16
MAINTAINER Hypothes.is Project and contributors

# System dependencies
RUN apt-add-repository ppa:brightbox/ruby-ng
RUN apt-get -q -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --no-install-recommends install \
  build-essential \
  git \
  libevent-dev \
  libffi-dev \
  libpq-dev \
  libyaml-dev \
  nodejs \
  npm \
  python-dev \
  python-pip \
  python-virtualenv \
  ruby2.2 \
  ruby2.2-dev

# Provide /usr/bin/node as well as /usr/bin/nodejs
RUN update-alternatives --install /usr/bin/node node /usr/bin/nodejs 10

# Clean apt state
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Base environment
RUN pip install -U pip virtualenv
RUN npm install -g npm
RUN gem install compass
RUN virtualenv /srv/h
RUN mkdir -p /src/h
ENV PATH=/srv/h/bin:/src/h/bin:/src/h/node_modules/.bin:$PATH
WORKDIR /src/h

# Python dependencies
ADD CHANGES.txt README.rst       /src/h/
ADD setup.* requirements.txt     /src/h/
ADD versioneer.py                /src/h/
ADD h/_version.py                /src/h/h/
RUN pip install -r requirements.txt

# Node dependencies
ADD package.json                 /src/h/
RUN npm install --production

# Install the h application
ADD Makefile                     /src/h/
ADD gunicorn.conf.py             /src/h/
ADD bin                          /src/h/bin
ADD conf                         /src/h/conf
ADD h                            /src/h/h
RUN pip install -r requirements.txt

# Services (for runit)
ADD ./svc /etc/service

# Startup and ports
ENTRYPOINT ["/sbin/my_init"]
CMD []
EXPOSE 8000
