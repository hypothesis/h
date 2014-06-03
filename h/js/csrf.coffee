imports = ['h.helpers']


configure = ['$httpProvider', ($httpProvider) ->
  # Use the Pyramid XSRF header name
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'

  # Track the token with an interceptor because the cookies will not be
  # available on extension requests due to cross-origin restrictions.
  $httpProvider.interceptors.push ['baseURI', (baseURI) ->
    defaults = $httpProvider.defaults
    token = null

    _getToken = (response) ->
      data = response.data
      format = response.headers 'content-type'
      if format?.match /^application\/json/
        if data.csrf?
          token = data.csrf
          delete data.csrf
      response

    _setToken = (config) ->
      if config.url.match(baseURI)?.index == 0
        cookieName = config.xsrfCookieName || defaults.xsrfCookieName
        headerName = config.xsrfHeaderName || defaults.xsrfHeaderName
        config.headers[headerName] ?= token
      config

    request: _setToken
    response: _getToken
    responseError: _getToken
  ]
]


angular.module('h.csrf', imports, configure)
