$ = Annotator.$

extract = extract = (obj, keys...) ->
  ret = {}
  ret[key] = obj[key] for key in keys when obj.hasOwnProperty(key)
  ret

class Annotator.Plugin.Bridge extends Annotator.Plugin
  constructor: (elem, options) ->
    super
    discovery = new window.CrossFrameDiscovery(window, extract(options, 'server'))
    bridge = new window.CrossFrameBridge(extract(options, 'scope'))

    syncOpts = extract(options, 'on', 'emit', 'formatter', 'parser')
    annotationSync = new window.AnnotationSync(syncOpts, @bridge)

    this.pluginInit = ->
      onDiscoveryCallback = (source, origin, token) ->
        bridge.createChannel(source, origin, token)
      discovery.startDiscovery(onDiscoveryCallback)

    this.destroy = ->
      # super doesnt work here :(
      Annotator.Plugin::destroy.apply(this, arguments)
      discovery.stopDiscovery()

    this.sync = (annotations, cb) ->
      annotationSync.sync(annotations, cb)

    this.on = (event, fn) ->
      bridge.on(event, fn)

    this.notify = (message) ->
      bridge.notify(message)

    this.onConnect = (fn) ->
      bridge.onConnect(fn)
