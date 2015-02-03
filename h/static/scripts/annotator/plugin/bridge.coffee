$ = Annotator.$

class Annotator.Plugin.Bridge extends Annotator.Plugin
  constructor: (elem, options) ->
    super
    discovery = new window.CrossFrameDiscovery(window, options.discoveryOptions)
    bridge = new window.CrossFrameBridge(options.bridgeOptions)
    annotationSync = new window.AnnotationSync(options.annotationSyncOptions, @bridge)

    this.pluginInit = ->
      onDiscoveryCallback = (source, origin, token) ->
        bridge.createChannel(source, origin, token)
      discovery.startDiscovery(onDiscoveryCallback)

    this.destroy = ->
      Annotator.Plugin::destroy.apply(this, arguments) # super doesnt work here :(
      discovery.stopDiscovery()

    this.sync = (annotations, cb) ->
      annotationSync.sync(annotations, cb)

    this.on = (event, fn) ->
      bridge.on(event, fn)

    this.notify = (message) ->
      bridge.notify(message)

    this.onConnect = (fn) ->
      bridge.onConnect(fn)
