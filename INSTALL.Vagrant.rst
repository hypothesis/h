Installing Hypothes.is with Vagrant
######################

Running Hypothes.is on a VM enables development on Windows machines, and also provides a "clean box"
for testing dependencies.  The following instructions will use Vagrant to create and manage
a VirtualBox Ubuntu VM with Hypothes.is and all its dependencies on it.

Install Vagrant
---------------

Use your package manager of choice, e.g.:

.. code-block:: bash

    sudo apt-get vagrant

or download from http://vagrantup.com.


Bootstrapping the VM
--------------------

From the home directory of the h project (this directory) :

.. code-block:: bash

    vagrant up
    vagrant ssh
    cd /h
    ifconfig # note the eth0 inet addr value

Next edit the ``development.ini`` file and change ``host: localhost`` (around line 109)
to the IP address you found via ``ifconfig``.

Lastly, follow the directions in ``./INSTALL.rst``.   That's it.

Notes on Using the VM
---------------------

* The vagrant commands are very simple: ``vagrant up``, ``vagrant ssh``, ``vagrant halt``, ``vagrant destroy``
  and a few others.  ``vagrant help`` for explanations.
  
* This vagrant configuration forwards port 5000 from the guest to the host.  This means that from your
  host machine (and from outside), "http://localhost:5000" (or your hostname or 127.0.0.1)
  will be routed to the h server on the VM.

* All the configuration is contained in ``./Vagrantfile``.  In particular the exact set of software
  dependencies are encoded there, so ``./Vagrantfile`` will need to be updated if those change.


VM State
--------

VM state is normally preserved across runs (e.g. ``vagrant halt`` followed by ``vagrant run``).
This includes the h server state (the annotation database), installed software, etc.  

In addition, the h directory (this directory) is mirrored on the VM (at ``/h``).  Changes can be made to the directory
either on the host or the guest.  For example, you can edit code and invoke git while on the VM.

The command ``vagrant destroy`` destroys the current VM and its corresponding state, but does
not affect this directory.

The configuration process is run each time the VM is brought up; if this gets annoying, it is
possible to make a snapshot of the VM and use that instead. You can also add ``--no-provision``
to avoid re-running the bash installation-time scripts.


Notes for Windows Development
-----------------------------

If you are working with a Windows host, you want the shared directory to use Unix line endings.
Do that by configuring this git repository as follows:
 
.. code-block:: bash

    git config core.eol lf
    git config core.autocrlf input

You will probably also need to ``git reset --hard`` to re-extract all files with approproate line endings.
Do this *before* proceeding with bootstrapping.

