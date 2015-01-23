# Uses a channel between the sidebar and the attached providers to ensure
# the interface remains in sync.
class AnnotationUISync
  constructor: ($rootScope, $window, bridge, annotationUI) ->
    getAnnotationsByTags = (tags) ->
      tags.map(bridge.getAnnotationForTag, bridge)

    notifyHost = (message) ->
      for {channel, window} in bridge.links where window is $window.parent
        channel.notify(message)
        break

    hide = notifyHost.bind(null, method: 'hideFrame')
    show = notifyHost.bind(null, method: 'showFrame')

    channelListeners =
      back: hide
      open: show
      showEditor: show
      showAnnotations: (ctx, tags=[]) =>
        show()
        annotations = getAnnotationsByTags(tags)
        annotationUI.xorSelectedAnnotations(annotations)
      focusAnnotations: (ctx, tags=[]) =>
        annotations = getAnnotationsByTags(tags)
        annotationUI.focusAnnotations(annotations)
      toggleAnnotationSelection: (ctx, tags=[]) =>
        annotations = getAnnotationsByTags(tags)
        annotationUI.selectAnnotations(annotations)
      setTool: (ctx, name) =>
        annotationUI.tool = name
        bridge.notify(method: 'setTool' params: name)
      setVisibleHighlights: (ctx, state) =>
        annotationUI.visibleHighlights = Boolean(state)
        bridge.notify(method: 'setVisibleHighlights' params: state)

    for channel, listener in channelListeners
      bridge.on(channel, listener)
