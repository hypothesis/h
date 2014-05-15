class Notification extends Annotator.Notification
  @INFO: 'info'
  @ERROR: 'error'
  @SUCCESS: 'success'

  constructor: (options) ->
    element = $(@options.html).hide()[0]
    Annotator.Delegator.call(this, element, options)

  # Retain the fat arrow binding despite skipping the super-class constructor
  # XXX: replace with _appendElement override when we move to Annotator v2.
  show: (message, status = Notification.INFO) =>
    super
    @element.prependTo(document.body).slideDown()

  hide: =>
    super
    @element.slideUp => @element.remove()


class FlashProvider
  queues:
    '': []
    info: []
    error: []
    success: []
  notice: null

  $get: ->
    angular.bind this, this._flash

  _process: ->
    for q, msgs of @queues
      if msgs.length
        msg = msgs.shift()
        unless q then [q, msg] = msg
        notice = new Notification()
        notice.show(msg, q)
        break

  _flash: (queue, messages) ->
    if @queues[queue]?
      @queues[queue] = @queues[queue]?.concat messages
      this._process()


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
        $q.reject(data)
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
