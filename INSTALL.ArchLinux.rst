Installing Hypothes.is on ArchLinux
###################################

Install the following packages:

.. code-block:: bash

    python2-pip python2-virtualenv libyaml gcc git

From the Arch User Repository (AUR), obtain:

.. code-block:: bash

    coffee-script elasticsearch ruby-compass nodejs-uglify-js

Due to ArchLinux idiosyncracies where python 2 and python 3 are concerned, you need to run the following 
in the top directory (i.e., inside h/) for hypothesis to correctly use python 2:

.. code-block:: bash

    sed -i 's|env python|env python2|' run

DO NOT CHANGE references to "pip" in the bootstrap script to read "pip2" even if that is the executable that was installed above. Inside the virtualenv environment, "pip" is streated special, while "pip2" is ostensibly working until it tries to write to your global PYTHONPATH (which virtualenv is meant to prevent).

Before executing bootstrap it may be advisable to set the "index-url" in the [global] section of ~/.pip/pip.conf to a fast pip-mirror close to you. The default pip server had some severe bandwidth constraints in my case.

Once you are ready to bootstrap a local python environment (the script can be run unpriviliged since it won't touch your machine-wide python installation anyway) do the following:

.. code-block:: bash

    ./bootstrap

And go get a coffee.

To test things out, start elasticsearch locally by issuing:

.. code-block:: bash

    systemctl start elasticsearch.service

And type:

.. code-block:: bash

    ./run

Making the documentation
------------------------

In the top level directory, change into the virtual python environment that is used for development by running:

.. code-block:: bash

    . bin/activate

Then use pip to install the Sphinx documentation generator locally like so:

.. code-block:: bash

    pip install Sphinx

NOTE: not using a local version of Sphinx will fail to generate proper docs because the entire python environment is global.

Finally, cd into docs/ and make your favourite documentation target. I did:

.. code-block:: bash

    make html
