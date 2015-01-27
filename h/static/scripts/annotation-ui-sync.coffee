# Uses a channel between the sidebar and the attached providers to ensure
# the interface remains in sync.
class AnnotationUISync
  constructor: ($window, bridge, annotationSync, annotationUI) ->
    getAnnotationsByTags = (tags) ->
      tags.map(annotationSync.getAnnotationForTag, annotationSync)

    notifyHost = (message) ->
      for {channel, window} in bridge.links when window is $window.parent
        channel.notify(message)
        break

    hide = notifyHost.bind(null, method: 'hideFrame')
    show = notifyHost.bind(null, method: 'showFrame')

    channelListeners =
      back: hide
      open: show
      showEditor: show
      showAnnotations: (ctx, tags=[]) ->
        show()
        annotations = getAnnotationsByTags(tags)
        annotationUI.xorSelectedAnnotations(annotations)
      focusAnnotations: (ctx, tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.focusAnnotations(annotations)
      toggleAnnotationSelection: (ctx, tags=[]) ->
        annotations = getAnnotationsByTags(tags)
        annotationUI.selectAnnotations(annotations)
      setTool: (ctx, name) ->
        annotationUI.tool = name
        bridge.notify(method: 'setTool', params: name)
      setVisibleHighlights: (ctx, state) ->
        annotationUI.visibleHighlights = Boolean(state)
        bridge.notify(method: 'setVisibleHighlights', params: state)

    for own channel, listener of channelListeners
      bridge.on(channel, listener)

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
