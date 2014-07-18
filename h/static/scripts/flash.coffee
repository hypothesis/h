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


angular.module('h.flash', ['ngResource'])
.provider('flash', FlashProvider)
