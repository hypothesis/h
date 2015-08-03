# Uses a channel between the sidebar and the attached frames to ensure
# the interface remains in sync.
module.exports = class AnnotationUISync
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

    channelListeners =
      showAnnotations: (tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.selectAnnotations(annotations)
      focusAnnotations: (tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.focusAnnotations(annotations)
      toggleAnnotationSelection: (tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.xorSelectedAnnotations(annotations)
      setVisibleHighlights: (state) ->
        annotationUI.visibleHighlights = Boolean(state)
        bridge.call('setVisibleHighlights', state)

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
        channel.call('setVisibleHighlights', annotationUI.visibleHighlights)

    bridge.onConnect(onConnect)
