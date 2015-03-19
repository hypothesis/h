# Uses a channel between the sidebar and the attached providers to ensure
# the interface remains in sync.
class AnnotationUISync
  ###*
  # @name AnnotationUISync
  # @param {$window} $window An Angular window service.
  # @param {Bridge} bridge
  # @param {AnnotationSync} annotationSync
  # @param {AnnotationUI} annotationUI An instance of the AnnotatonUI service
  # @description
  # Listens for incoming events over the bridge concerning the annotation
  # interface and updates the applications internal state. It also ensures
  # that the messages are broadcast out to other frames.
  ###
  constructor: ($rootScope, $window, bridge, annotationSync, annotationUI) ->
    # Retrieves annotations from the annotationSync cache.
    getAnnotationsByTags = (tags) ->
      tags.map(annotationSync.getAnnotationForTag, annotationSync)

    # Sends a message to the host frame only.
    notifyHost = (message) ->
      for {channel, window} in bridge.links when window is $window.parent
        channel.notify(message)
        break

    # Send messages to host to hide/show sidebar iframe.
    hide = notifyHost.bind(null, method: 'hideFrame')
    show = notifyHost.bind(null, method: 'showFrame')


    channelListeners =
      back: hide
      open: show
      showEditor: show
      showAnnotations: (ctx, tags=[]) ->
        show()
        annotations = getAnnotationsByTags(tags)
        annotationUI.selectAnnotations(annotations)
      clearSelection: (ctx) ->
        $rootScope.$broadcast('clearSelection')
      focusAnnotations: (ctx, tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.focusAnnotations(annotations)
      toggleAnnotationSelection: (ctx, tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.xorSelectedAnnotations(annotations)
      setTool: (ctx, name) ->
        annotationUI.tool = name
        bridge.notify(method: 'setTool', params: name)
      setVisibleHighlights: (ctx, state) ->
        annotationUI.visibleHighlights = Boolean(state)
        bridge.notify(method: 'setVisibleHighlights', params: state)

    # Because the channel events are all outside of the angular framework we
    # need to inform Angular that it needs to re-check it's state and re-draw
    # any UI that may have been affected by the handlers.
    ensureDigest = (fn) ->
      ->
        fn.apply(this, arguments)
        $rootScope.$digest()

    for own channel, listener of channelListeners
      bridge.on(channel, ensureDigest(listener))

    onConnect = (channel, source) ->
      # Allow the host to define its own state
      unless source is $window.parent
        channel.notify
          method: 'setTool'
          params: annotationUI.tool

        channel.notify
          method: 'setVisibleHighlights'
          params: annotationUI.visibleHighlights

    bridge.onConnect(onConnect)

angular.module('h').value('AnnotationUISync', AnnotationUISync)
