class FlashProvider
  queues:
    '': []
    info: []
    error: []
    success: []
  notice: null
  timeout: null

  constructor: ->
    # Configure notification classes
    angular.extend Annotator.Notification,
      INFO: 'info'
      ERROR: 'error'
      SUCCESS: 'success'

  _process: ->
    @timeout = null
    for q, msgs of @queues
      if msgs.length
        msg = msgs.shift()
        unless q then [q, msg] = msg
        if annotator.isOpen()
          notice = Annotator.showNotification msg, q
          @timeout = this._wait =>
            # work around Annotator.Notification not removing classes
            for _, klass of notice.options.classes
              notice.element.removeClass klass
            this._process()
        else
          annotator.host.notify
            method: "showNotification"
            params:
              message: msg
              type: q
          @timeout = this._wait =>
            annotator.host.notify
              method: "removeNotification"
            this._process()
        break

  _flash: (queue, messages) ->
    if @queues[queue]?
      @queues[queue] = @queues[queue]?.concat messages
      this._process() unless @timeout?

  $get: ['$timeout', ($timeout) ->
    this._wait = (cb) -> $timeout cb, 5000
    angular.bind this, this._flash
  ]


flashInterceptor = ['$q', 'flash', ($q, flash) ->
  _intercept = (response) ->
    data = response.data
    format = response.headers 'content-type'
    if format?.match /^application\/json/
      if data.flash?
        for q, msgs of data.flash
          # Workaround for horus returning the same error for
          # both the username and the password field, and thus
          # flashing the same error message twice
          if msgs.length is 2 and
          msgs[0] is "Invalid username or password." and
          msgs[1] is msgs[0]
            msgs.pop()
            ignoreStatus = true
          flash q, msgs

      if data.status is 'failure'
        flash 'error', data.reason unless ignoreStatus
        $q.reject(data.reason)
      else if data.status is 'okay' and data.model
        response.data = data.model
        response
      else
        response
    else
      response
  response: _intercept
  responseError: _intercept
]


angular.module('h.flash', ['ngResource'])
.provider('flash', FlashProvider)
.factory('flashInterceptor', flashInterceptor)
.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.interceptors.push 'flashInterceptor'
])