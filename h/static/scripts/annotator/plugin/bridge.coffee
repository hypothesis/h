$ = Annotator.$

class Annotator.Plugin.Bridge extends Annotator.Plugin
  constructor: (elem, options) ->
    super
    @discovery = new window.CrossFrameDiscovery(window, options.discoveryOptions)
    @bridge = new window.CrossFrameBridge(options.bridgeOptions)
    @annotationSync = new window.AnnotationSync(options.annotationSyncOptions, @bridge)

  pluginInit: ->
    onDiscoveryCallback = (source, origin, token) =>
      @bridge.createChannel(source, origin, token)
    @discovery.startDiscovery(onDiscoveryCallback)

  destroy: ->
    super
    @discovery.stopDiscovery()
    return

  sync: (annotations, cb) ->
    @annotationSync.sync(annotations, cb)
