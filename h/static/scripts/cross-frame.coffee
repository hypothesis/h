# Instantiates all objects used for cross frame discovery and communication.
module.exports = class CrossFrame
  this.$inject = [
    '$rootScope', '$document', '$window', 'store', 'annotationUI'
    'Discovery', 'bridge',
    'AnnotationSync', 'AnnotationUISync'
  ]
  constructor: (
    $rootScope, $document, $window, store, annotationUI
    Discovery, bridge,
    AnnotationSync, AnnotationUISync
  ) ->
    @frames = []

    createDiscovery = ->
      options =
        server: true
      new Discovery($window, options)

    createAnnotationSync = ->
      whitelist = ['$orphan', '$highlight', 'target', 'document', 'uri']
      options =
        formatter: (annotation) ->
          formatted = {}
          for k, v of annotation when k in whitelist
            formatted[k] = v
          formatted
        parser: (annotation) ->
          parsed = new store.AnnotationResource()
          for k, v of annotation when k in whitelist
            parsed[k] = v
          parsed
        emit: (args...) ->
          $rootScope.$apply ->
            $rootScope.$emit.call($rootScope, args...)
        on: (event, handler) ->
          $rootScope.$on(event, (event, args...) -> handler.apply(this, args))

      new AnnotationSync(bridge, options)

    createAnnotationUISync = (annotationSync) ->
      new AnnotationUISync($rootScope, $window, bridge, annotationSync, annotationUI)

    addFrame = (channel) =>
      channel.call 'getDocumentInfo', (err, info) =>
        if err
          channel.destroy()
        else
          $rootScope.$apply =>
            @frames.push({channel: channel, uri: info.uri})

    this.connect = ->
      discovery = createDiscovery()

      bridge.onConnect(addFrame)
      annotationSync = createAnnotationSync()
      annotationUISync = createAnnotationUISync(annotationSync)

      onDiscoveryCallback = (source, origin, token) ->
        bridge.createChannel(source, origin, token)
      discovery.startDiscovery(onDiscoveryCallback)

      this.call = bridge.call.bind(bridge)

    this.call = -> throw new Error('connect() must be called before call()')
