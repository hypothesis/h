Installing Hypothes.is on Debian
######################

To install the dependencies, run these commands::

    $ yum install --nogpgcheck http://nodejs.tchol.org/repocfg/fedora/nodejs-stable-release.noarch.rpm
    $ yum install nodejs-compat-symlinks npm python-{pip,virtualenv} rubygem-{compass,sass}

Make sure to install at least version 0.12.2 of rubygem-compass.
If not available as an RPM, you can use this::

    $ gem install compass

After that::

    $ npm install -g coffee-script handlebars uglify-js

Follow the instructions at elastisearch_rpm_ to build and install the elasticsearch server,
but don't start it just yet: 

Before you start the elasticsearch daemon:

 - Edit the /etc/init.d/elasticsearch script and insert the following line
   at the beginning of the script (before it sources /etc/rc.d/init.d/functions)::

     SYSTEMCTL_SKIP_REDIRECT=1

 - In /usr/share/elasticsearch/bin/elasticsearch.in.sh,
    comment out the javaopts that reduces the per-thread stack::

     #JAVA_OPTS="$JAVA_OPTS -Xss128k"

After installing the above, create the virtualenv,
as described in the README.rst

(Run the commands from the directory where you've cloned the repository.)

.. _elasticsearch_rpm: https://github.com/tavisto/elasticsearch-rpms
