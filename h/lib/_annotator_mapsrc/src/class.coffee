# Public: Delegator is the base class that all of Annotators objects inherit
# from. It provides basic functionality such as instance options, event
# delegation and pub/sub methods.
class Delegator
  # Public: Events object. This contains a key/pair hash of events/methods that
  # should be bound. See Delegator#addEvents() for usage.
  events: {}

  # Public: Options object. Extended on initialisation.
  options: {}

  # A jQuery object wrapping the DOM Element provided on initialisation.
  element: null

  # Public: Constructor function that sets up the instance. Binds the @events
  # hash and extends the @options object.
  #
  # element - The DOM element that this intance represents.
  # options - An Object literal of options.
  #
  # Examples
  #
  #   element  = document.getElementById('my-element')
  #   instance = new Delegator(element, {
  #     option: 'my-option'
  #   })
  #
  # Returns a new instance of Delegator.
  constructor: (element, options) ->
    @options = $.extend(true, {}, @options, options)
    @element = $(element)

    this.on = this.subscribe
    this.addEvents()

  # Binds the function names in the @events Object to thier events.
  #
  # The @events Object should be a set of key/value pairs where the key is the
  # event name with optional CSS selector. The value should be a String method
  # name on the current class. 
  #
  # Examples
  #
  #   # This will bind the clickedElement() method to the click event on @element.
  #   @options = {"click": "clickedElement"}
  #
  #   # This will delegate the submitForm() method to the submit event on the
  #   # form within the @element.
  #   @options = {"form submit": "submitForm"}
  #
  #   # This will bind the updateAnnotationStore() method to the custom
  #   # annotation:save event. NOTE: Because this is a custom event the 
  #   # Delegator#subscribe() method will be used and updateAnnotationStore() 
  #   # will not recieve an event parameter like the previous two examples.
  #   @options = {"annotation:save": "updateAnnotationStore"}
  #
  # Returns nothing.
  addEvents: ->
    for sel, functionName of @events
      [selector..., event] = sel.split ' '
      this.addEvent selector.join(' '), event, functionName

  # Binds an event to a callback function represented by a String. An optional
  # bindTo selector can be provided in order to watch for events on a child
  # element.
  #
  # The event can be any standard event supported by jQuery or a custom String.
  # If a custom string is used the callback function will not recieve an
  # event object as it's first parameter.
  #
  # bindTo       - Selector String matching child elements. (default: @element)
  # event        - The event to listen for.
  # functionName - A String function name to bind to the event.
  #
  # Examples
  #
  #   # Listens for all click events on instance.element.
  #   instance.addEvent('', 'click', 'onClick')
  #
  #   # Delegates the instance.onInputFocus() method to focus events on all
  #   # form inputs within instance.element.
  #   instance.addEvent('form :input', 'focus', 'onInputFocus')
  #
  # Returns itself.
  addEvent: (bindTo, event, functionName) ->
    closure = => this[functionName].apply(this, arguments)

    isBlankSelector = typeof bindTo is 'string' and bindTo.replace(/\s+/g, '') is ''

    bindTo = @element if isBlankSelector

    if typeof bindTo is 'string'
      @element.delegate bindTo, event, closure
    else
      if this.isCustomEvent(event)
        this.subscribe event, closure
      else
        $(bindTo).bind event, closure

    this

  # Checks to see if the provided event is a DOM event supported by jQuery or
  # a custom user event.
  #
  # event - String event name.
  #
  # Examples
  #
  #   this.isCustomEvent('click')              # => false
  #   this.isCustomEvent('mousedown')          # => false
  #   this.isCustomEvent('annotation:created') # => true
  #
  # Returns true if event is a custom user event.
  isCustomEvent: (event) ->
    [event] = event.split('.')
    $.inArray(event, Delegator.natives) == -1

  # Public: Fires an event and calls all subscribed callbacks with any parameters
  # provided. This is essentially an alias of @element.triggerHandler() but
  # should be used to fire custom events.
  #
  # NOTE: Events fired using .publish() will not bubble up the DOM.
  #
  # event  - A String event name.
  # params - An Array of parameters to provide to callbacks.
  #
  # Examples
  #
  #   instance.subscribe('annotation:save', (msg) -> console.log(msg))
  #   instance.publish('annotation:save', ['Hello World'])
  #   # => Outputs "Hello World"
  #
  # Returns itself.
  publish: () ->
    @element.triggerHandler.apply @element, arguments
    this

  # Public: Listens for custom event which when published will call the provided
  # callback. This is essentially a wrapper around @element.bind() but removes
  # the event parameter that jQuery event callbacks always recieve. These
  # parameters are unnessecary for custom events.
  #
  # event    - A String event name.
  # callback - A callback function called when the event is published.
  #
  # Examples
  #
  #   instance.subscribe('annotation:save', (msg) -> console.log(msg))
  #   instance.publish('annotation:save', ['Hello World'])
  #   # => Outputs "Hello World"
  #
  # Returns itself.
  subscribe: (event, callback) ->
    closure = -> callback.apply(this, [].slice.call(arguments, 1))

    # Ensure both functions have the same unique id so that jQuery will accept
    # callback when unbinding closure.
    closure.guid = callback.guid = ($.guid += 1)

    @element.bind event, closure
    this

  # Public: Unsubscribes a callback from an event. The callback will no longer
  # be called when the event is published.
  #
  # event    - A String event name.
  # callback - A callback function to be removed.
  #
  # Examples
  #
  #   callback = (msg) -> console.log(msg)
  #   instance.subscribe('annotation:save', callback)
  #   instance.publish('annotation:save', ['Hello World'])
  #   # => Outputs "Hello World"
  #
  #   instance.unsubscribe('annotation:save', callback)
  #   instance.publish('annotation:save', ['Hello Again'])
  #   # => No output.
  #
  # Returns itself.
  unsubscribe: ->
    @element.unbind.apply @element, arguments
    this

# Native jQuery events that should recieve an event object. Plugins can
# add thier own methods to this if required.
Delegator.natives = do ->
  specials = (key for own key, val of jQuery.event.special)
  """
  blur focus focusin focusout load resize scroll unload click dblclick
  mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave
  change select submit keydown keypress keyup error
  """.split(/[^a-z]+/).concat(specials)
