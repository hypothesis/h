Installing Hypothes.is on OS X ML
######################

Install Homebrew:

.. code-block:: bash

    ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"

Install python:

.. code-block:: bash

    brew install python

Install virtualenv:

.. code-block:: bash

    pip install virtualenv

Install Node and other required tools:

.. code-block:: bash

    gem install compass
    brew install node
    npm -g install uglify-js
    npm -g install handlebars
    npm -g install coffee-script

Add the tools' path to the $PATH variable:

.. code-block:: bash

    echo "export PATH=/usr/local/share/python:$PATH" >> ~/.profile
    echo "export PATH=/usr/local/share/npm/bin:$PATH" >> ~/.profile

Install Elasticsearch:

.. code-block:: bash

    brew install elasticsearch

To have Elasticsearch run automatically at login:

.. code-block:: bash

    ln -sfv /usr/local/opt/elasticsearch/*.plist ~/Library/LaunchAgents
    launchctl load ~/Library/LaunchAgents/homebrew.mxcl.elasticsearch.plist

To launch it manually without launchctl:

.. code-block:: bash

    elasticsearch -f -D es.config=/usr/local/opt/elasticsearch/config/elasticsearch.yml

After installing the above, create the virtualenv, as described in the INSTALL.rst

(Run the commands from the directory where you've cloned the repository.)
