class FlashProvider
  queues:
    '': []
    info: []
    error: []
    success: []
  notice: null

  constructor: ->
    # Configure notification classes
    angular.extend Annotator.Notification,
      INFO: 'info'
      ERROR: 'error'
      SUCCESS: 'success'

  _process: ->
    for q, msgs of @queues
      if msgs.length
        msg = msgs.shift()
        unless q then [q, msg] = msg
        notice = new Hypothesis.Notification()
        notice.show(msg, q)
        notice.element.hide().slideDown()
        this._wait =>
          notice.element.slideUp ->
            notice.element.remove()
        break

  _flash: (queue, messages) ->
    if @queues[queue]?
      @queues[queue] = @queues[queue]?.concat messages
      this._process()

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
          flash q, msgs

      if data.status is 'failure'
        flash 'error', data.reason
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
