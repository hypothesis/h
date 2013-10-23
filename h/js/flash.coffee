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
        notice = Annotator.showNotification msg, q
        @timeout = this._wait =>
          # work around Annotator.Notification not removing classes
          for _, klass of notice.options.classes
            notice.element.removeClass klass
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
  response: (response) ->
    data = response.data
    format = response.headers 'content-type'
    if format?.match /^application\/json/
      if data.flash?
        flash q, msgs for q, msgs of data.flash

      if data.status is 'failure'
        flash 'error', data.reason
        $q.reject(data.reason)
      else if data.status is 'okay'
        response.data = data.model
        response
    else
      response
]


angular.module('h.flash', ['ngResource'])
.provider('flash', FlashProvider)
.factory('flashInterceptor', flashInterceptor)
.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.interceptors.push 'flashInterceptor'
])