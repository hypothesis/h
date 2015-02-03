assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Plugin.Bridge', ->
  fakeCFDiscovery = null
  fakeCFBridge = null
  fakeAnnotationSync = null
  sandbox = sinon.sandbox.create()

  createBridge = (options) ->
    defaults =
      annotationSyncOptions:
        on: sandbox.stub()
        emit: sandbox.stub()
    element = document.createElement('div')
    return new Annotator.Plugin.Bridge(element, $.extend(true, {}, defaults, options))

  beforeEach ->
    fakeCFDiscovery =
      startDiscovery: sandbox.stub()
      stopDiscovery: sandbox.stub()

    fakeCFBridge =
      createChannel: sandbox.stub()
      onConnect: sandbox.stub()
      notify: sandbox.stub()
      on: sandbox.stub()

    fakeAnnotationSync =
      sync: sandbox.stub()

    window.AnnotationSync = sandbox.stub().returns(fakeAnnotationSync)
    window.CrossFrameDiscovery = sandbox.stub().returns(fakeCFDiscovery)
    window.CrossFrameBridge = sandbox.stub().returns(fakeCFBridge)

  afterEach ->
    delete window.AnnotationSync
    delete window.CrossFrameBridge
    delete window.CrossFrameDiscovery
    sandbox.restore()

  describe 'constructor', ->
    it 'instantiates the CrossFrameDiscovery component', ->
      createBridge()
      assert.called(CrossFrameDiscovery)
      assert.calledWith(CrossFrameDiscovery, window)

    it 'passes the options along to the bridge', ->
      createBridge(discoveryOptions: {server: true})
      assert.called(CrossFrameDiscovery)
      assert.calledWith(CrossFrameDiscovery, window, server: true)

    it 'instantiates the CrossFrameBridge component', ->
      createBridge()
      assert.called(CrossFrameBridge)
      assert.calledWith(CrossFrameDiscovery)

    it 'passes the options along to the bridge', ->
      createBridge(bridgeOptions: {scope: 'myscope'})
      assert.called(CrossFrameBridge)
      assert.calledWith(CrossFrameBridge, scope: 'myscope')

    it 'instantiates the AnnotationSync component', ->
      createBridge()
      assert.called(AnnotationSync)

    it 'passes along options to AnnotationSync', ->
      formatter = (x) -> x
      createBridge(annotationSyncOptions: {formatter: formatter})
      assert.called(AnnotationSync)
      assert.calledWith(AnnotationSync, {
        on: sinon.match.func
        emit: sinon.match.func
        formatter: formatter
      })

  describe '.pluginInit', ->
    it 'starts the discovery of new channels', ->
      bridge = createBridge()
      bridge.pluginInit()
      assert.called(fakeCFDiscovery.startDiscovery)

    it 'creates a channel when a new frame is discovered', ->
      bridge = createBridge()
      bridge.pluginInit()
      fakeCFDiscovery.startDiscovery.yield('SOURCE', 'ORIGIN', 'TOKEN')
      assert.called(fakeCFBridge.createChannel)
      assert.calledWith(fakeCFBridge.createChannel, 'SOURCE', 'ORIGIN', 'TOKEN')

  describe '.destroy', ->
    it 'stops the discovery of new frames', ->
      bridge = createBridge()
      bridge.destroy()
      assert.called(fakeCFDiscovery.stopDiscovery)

  describe '.sync', ->
    it 'syncs the annotations with the other frame', ->
      bridge = createBridge()
      bridge.sync()
      assert.called(fakeAnnotationSync.sync)

  describe '.on', ->
    it 'proxies the call to the bridge', ->
      bridge = createBridge()
      bridge.on('event', 'arg')
      assert.calledWith(fakeCFBridge.on, 'event', 'arg')

  describe '.notify', ->
    it 'proxies the call to the bridge', ->
      bridge = createBridge()
      bridge.notify(method: 'method')
      assert.calledWith(fakeCFBridge.notify, method: 'method')

  describe '.onConnect', ->
    it 'proxies the call to the bridge', ->
      bridge = createBridge()
      fn = ->
      bridge.onConnect(fn)
      assert.calledWith(fakeCFBridge.onConnect, fn)
