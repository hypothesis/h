class Annotator.Host extends Annotator
  # Override the events to be bound on Annotator#element to get rid of
  # the highlight hover behaviour.
  events:
    ".annotator-adder button click":     "onAdderClick"
    ".annotator-adder button mousedown": "onAdderMousedown"

  constructor: (element, options) ->
    super element, options

    # Establish cross-domain communication
    @host = new easyXDM.WidgetManager
      container: element

    #@host.subscribe 'annotator'
    #@host.: (event, label, successFn, errorFn) =>
    #      this.subscribe event, (args...) =>
    #        @rpc.publish event, args...
    #      do successFn
    #    publish: (event, args, successFn, errorFn) =>
    #      this.publish event, args
    #      do successFn
    #  remote:
    #    subscribe:
    #    publish:
    #})

  # Sets up the selection event listeners to watch mouse actions on the document.
  #
  # Returns itself for chaining.
  _setupDocumentEvents: ->
    $(document).bind({
      "mouseup": this.checkForEndSelection
    })
    this
