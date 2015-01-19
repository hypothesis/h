escape = (html) ->
  html
    .replace(/&(?!\w+;)/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')


class Notification
  # Default options.
  options:
    html: "<div class='annotator-notice'></div>"
    classes:
      show:    "annotator-notice-show"
      info:    "annotator-notice-info"
      success: "annotator-notice-success"
      error:   "annotator-notice-error"

  @INFO: 'info'
  @ERROR: 'error'
  @SUCCESS: 'success'

  constructor: (options) ->
    element = $(@options.html).hide()[0]
    @element = $(element)
    @options = $.extend(true, {}, @options, options)

  # Retain the fat arrow binding despite skipping the super-class constructor
  # XXX: replace with _appendElement override when we move to Annotator v2.
  show: (message, status = Notification.INFO) =>
    @currentStatus = status
    $(@element)
      .addClass(@options.classes.show)
      .addClass(@options.classes[@currentStatus])
      .html(escape(message || ""))

    setTimeout @hide, 5000
    @element.prependTo(document.body).slideDown()

  hide: =>
    @currentStatus ?= Annotator.Notification.INFO
    $(@element)
      .removeClass(@options.classes.show)
      .removeClass(@options.classes[@currentStatus])
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


angular.module('h')
.provider('flash', FlashProvider)
