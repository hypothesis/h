Installing Hypothes.is on OSX
#############################

Run the following commands from the directory where you've cloned this repository.

Install `Homebrew
<http://brew.sh/>`_:

.. code-block:: bash

    ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

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

Add the tools' path to the $PATH variable:

.. code-block:: bash

    echo "export PATH=/usr/local/share/python:\$PATH" >> ~/.profile
    source ~/.profile

Install Elasticsearch
---------------------

`Elasticsearch
<http://www.elasticsearch.org/>`_ is required in order to store annotations
locally. Take care that you install a version that meets the requirements listed
in `<INSTALL.rst>`_. You can check what is available via Homebrew with:

.. code-block:: bash

    brew info elasticsearch

If an appropriate version is available then follow the instructions below,
otherwise get a version from `<http://www.elasticsearch.org/>`_.

.. code-block:: bash

    brew install elasticsearch

To have Elasticsearch run automatically at login:

.. code-block:: bash

    ln -sfv /usr/local/opt/elasticsearch/*.plist ~/Library/LaunchAgents
    launchctl load ~/Library/LaunchAgents/homebrew.mxcl.elasticsearch.plist

To launch it manually without launchctl:

.. code-block:: bash

    elasticsearch -f -D es.config=/usr/local/opt/elasticsearch/config/elasticsearch.yml

Next Steps
----------

After installing the above, create the virtualenv, as described in `<INSTALL.rst>`_.
