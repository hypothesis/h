assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Plugin.Bridge', ->
  Bridge = null
  fakeCFDiscovery = null
  fakeBridge = null
  fakeAnnotationSync = null
  sandbox = sinon.sandbox.create()

  createBridge = (options) ->
    defaults =
      on: sandbox.stub()
      emit: sandbox.stub()
    element = document.createElement('div')
    return new Annotator.Plugin.Bridge(element, $.extend({}, defaults, options))

  beforeEach ->
    fakeCFDiscovery =
      startDiscovery: sandbox.stub()
      stopDiscovery: sandbox.stub()

    fakeBridge =
      createChannel: sandbox.stub()
      onConnect: sandbox.stub()
      notify: sandbox.stub()
      on: sandbox.stub()

    fakeAnnotationSync =
      sync: sandbox.stub()

    Bridge = Annotator.Plugin.Bridge
    sandbox.stub(Bridge, 'AnnotationSync').returns(fakeAnnotationSync)
    sandbox.stub(Bridge, 'CrossFrameDiscovery').returns(fakeCFDiscovery)
    sandbox.stub(Bridge, 'Bridge').returns(fakeBridge)

  afterEach ->
    sandbox.restore()

  describe 'constructor', ->
    it 'instantiates the CrossFrameDiscovery component', ->
      createBridge()
      assert.called(Bridge.CrossFrameDiscovery)
      assert.calledWith(Bridge.CrossFrameDiscovery, window)

    it 'passes the options along to the bridge', ->
      createBridge(server: true)
      assert.called(Bridge.CrossFrameDiscovery)
      assert.calledWith(Bridge.CrossFrameDiscovery, window, server: true)

    it 'instantiates the Bridge component', ->
      createBridge()
      assert.called(Bridge.Bridge)
      assert.calledWith(Bridge.CrossFrameDiscovery)

    it 'passes the options along to the bridge', ->
      createBridge(scope: 'myscope')
      assert.called(Bridge.Bridge)
      assert.calledWith(Bridge.Bridge, scope: 'myscope')

    it 'instantiates the AnnotationSync component', ->
      createBridge()
      assert.called(Bridge.AnnotationSync)

    it 'passes along options to AnnotationSync', ->
      formatter = (x) -> x
      createBridge(formatter: formatter)
      assert.called(Bridge.AnnotationSync)
      assert.calledWith(Bridge.AnnotationSync, fakeBridge, {
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
      assert.called(fakeBridge.createChannel)
      assert.calledWith(fakeBridge.createChannel, 'SOURCE', 'ORIGIN', 'TOKEN')

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
      assert.calledWith(fakeBridge.on, 'event', 'arg')

  describe '.notify', ->
    it 'proxies the call to the bridge', ->
      bridge = createBridge()
      bridge.notify(method: 'method')
      assert.calledWith(fakeBridge.notify, method: 'method')

  describe '.onConnect', ->
    it 'proxies the call to the bridge', ->
      bridge = createBridge()
      fn = ->
      bridge.onConnect(fn)
      assert.calledWith(fakeBridge.onConnect, fn)
