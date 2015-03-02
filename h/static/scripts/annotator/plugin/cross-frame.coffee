Annotator = require('annotator')

$ = Annotator.$

# Extracts individual keys from an object and returns a new one.
extract = extract = (obj, keys...) ->
  ret = {}
  ret[key] = obj[key] for key in keys when obj.hasOwnProperty(key)
  ret

# Class for establishing a messaging connection to the parent sidebar as well
# as keeping the annotation state in sync with the sidebar application, this
# frame acts as the bridge client, the sidebar is the server. This plugin
# can also be used to send messages through to the sidebar using the
# notify method.
CrossFrame = class Annotator.Plugin.CrossFrame extends Annotator.Plugin
  constructor: (elem, options) ->
    super

    opts = extract(options, 'server')
    discovery = new CrossFrame.Discovery(window, opts)

    opts = extract(options, 'scope')
    bridge = new CrossFrame.Bridge(opts)

    opts = extract(options, 'on', 'emit', 'formatter', 'parser')
    annotationSync = new CrossFrame.AnnotationSync(bridge, opts)

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

exports.CrossFrame = CrossFrame
