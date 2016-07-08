Client dev install
==================

The code for the Hypothesis client (the sidebar) lives in a `Git repo named
client`_. Follow this section to get the client running in a local development
environment.

.. seealso::

   The development version of the Hypothesis client currently requires a
   development version of the Hypothesis website and API, so you should follow
   :doc:`website` before following this page.

To install the Hypothesis client in a local development environment:

1. Clone the ``client`` git repo and ``cd`` into it:

   .. code-block:: bash

      git clone https://github.com/hypothesis/client.git
      cd client

2. Install the client's JavaScript dependencies:

   .. code-block:: bash

      npm install

3. Run the client's test to make sure everything's working:

   .. code-block:: bash

      make test

4. Link your website development environment to your development client.
   Run ``npm link`` in the ``client`` directory then ``npm link hypothesis``
   in the ``h`` directory:

   .. code-block:: bash

      client> npm link
      client> cd ../h
      h> npm link hypothesis

   .. tip::

      If you get a *permission denied* error when running ``npm link`` you
      probably need to tell npm to install packages into a directory in your
      home directory that you have permission to write to. On linux:

      .. code-block:: bash

         npm config set prefix /home/<YOUR_USERNAME>/npm

      On macOS:

      .. code-block:: bash

         npm config set prefix /Users/<YOUR_USERNAME>/npm

      npm will now install executable files into ``$HOME/npm/bin``, so add that
      directory to your ``$PATH``.

   Both your website development environment and the live reload server (see
   below) in your client development environment will now use your
   development client instead of the built client from npm.

   To unlink your website run ``npm unlink hypothesis`` then ``make clean`` in
   the ``h`` directory, your website development environment and the live
   reload server will both go back to using the built client from npm:

   .. code-block:: bash

      h> npm unlink hypothesis
      h> make clean dev

5. You can now test the client in a web browser by running the live reload
   server.

   .. note::

      The live reload server uses the
      *Hypothesis client from your website development environment*,
      not the client from your client development environment!

      By default your website dev env serves up the built client from npm.
      Make sure you've linked your website dev env to your client dev env
      (see above) so that your website serves up the client from your client
      dev env, then the live reload server will use your dev client as well.

   First run the web service on http://localhost:5000/, the client won't work
   without this because it sends HTTP requests to http://localhost:5000/ to
   fetch and to save annotations. In the ``h`` directory run:

   .. code-block:: bash

      h> make dev

   Now in another terminal, in the ``client`` directory, run the live reload
   server:

   .. code-block:: bash

      client> gulp watch

   Now open http://localhost:3000/ in a browser to see the client running in
   the live reload server. The live reload server automatically reloads the
   client whenever you modify any of its styles, templates or scripts.


.. include:: targets.rst
