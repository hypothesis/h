$ = Annotator.$

# Extracts individual keys from an object and returns a new one.
extract = extract = (obj, keys...) ->
  ret = {}
  ret[key] = obj[key] for key in keys when obj.hasOwnProperty(key)
  ret

Bridge = class Annotator.Plugin.Bridge extends Annotator.Plugin
  constructor: (elem, options) ->
    super

    opts = extract(options, 'server')
    discovery = new Bridge.Discovery(window, opts)

    opts = extract(options, 'scope')
    bridge = new Bridge.Bridge(opts)

    opts = extract(options, 'on', 'emit', 'formatter', 'parser')
    annotationSync = new Bridge.AnnotationSync(bridge, opts)

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
