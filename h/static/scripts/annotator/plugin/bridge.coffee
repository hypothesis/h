$ = Annotator.$

class Annotator.Plugin.Bridge extends Annotator.Plugin

  constructor: (elem, options) ->
    super
    @discovery = new CrossFrameDiscovery(options.discoveryOptions)
    @bridge = new CrossFrameBridge(options.bridgeOptions)
    @annotationSync = new AnnotationSync(options.annotationSyncOptions, @bridge)

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
