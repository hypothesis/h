# -*- coding: utf-8 -*-
def includeme(config):
    """Include a local authorization server.

    Example INI file:

    .. code-block:: ini
        [app:h]
        api.token_endpoint: /api/token
    """
    config.include('.models')
    config.include('.schemas')
    config.include('.subscribers')
    config.include('.views')
