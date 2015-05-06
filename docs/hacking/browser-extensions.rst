Building the browser extensions
###############################

To build the browser extensions, use the ``hypothesis-buildext`` tool::

    usage: hypothesis-buildext [-h] config_uri {chrome,firefox} ...

    positional arguments:
      config_uri        paster configuration URI

    optional arguments:
      -h, --help        show this help message and exit

    browser:
      {chrome,firefox}
        chrome          build the Google Chrome extension
        firefox         build the Mozilla Firefox extension

At this point, a working extension should exist in either ``./build/chrome``
or ``./build/firefox``. If the development configuration was used, static
assets are loaded from the server. Start the application and ensure that the
assets are built by visiting the start page or by running the ``assets``
command::

    usage: hypothesis assets [-h] config_uri

    positional arguments:
      config_uri  paster configuration URI

    optional arguments:
      -h, --help  show this help message and exit

