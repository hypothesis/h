Installing Hypothes.is on ArchLinux
###################################

Install the following packages::

    python2-pip python2-virtualenv libpqxx gcc git

From the Arch User Repository (AUR), obtain::

    coffee-script elasticsearch ruby-compass nodejs-uglify-js

Due to ArchLinux idiosyncracies where python 2 and python 3 are concerned, you need to run the following 
in the top directory (i.e., inside h/) for hypothesis to correctly use python 2::

    sed -i 's|virtualenv |virtualenv2 --distribute |g' bootstrap
    sed -i 's|env python|env python2|' run

NOTE: I added --distribute as flag to the command line of virtualenv because I got errors with the default "setuptools". YMMV

DO NOT CHANGE references to "pip" in the bootstrap script to read "pip2" even if that is the executable that was installed above. Inside the virtualenv environment, "pip" is streated special, while "pip2" is ostensibly working until it tries to write to your global PYTHONPATH (which virtualenv is meant to prevent).

If you want to see what is going during bootstrap, make the script more verbose by removing pipes to /dev/null::

    sed -i 's|[12]> */dev/null||g' bootstrap

Before executing bootstrap it may be advisable to set the "index-url" in the [global] section of ~/.pip/pip.conf to a fast pip-mirror close to you. The default pip server had some severe bandwidth constraints in my case.

Once you are ready to bootstrap a local python environment (the script can be run unpriviliged since it won't touch your machine-wide python installation anyway) do the following::

    ./bootstrap

And go get a coffee.

To test things out, start elasticsearch locally by issuing::

    systemctl start elasticsearch.service

And type::

    ./run

Making the documentation
------------------------

In the top level directory, change into the virtual python environment that is used for development by running::

    . bin/activate

Then use pip to install the Sphinx documentation generator locally like so::

    pip install Sphinx

NOTE: not using a local version of Sphinx will fail to generate proper docs because the entire python environment is global.

Finally, cd into docs/ and make your favourite documentation target. I did::

    make html
