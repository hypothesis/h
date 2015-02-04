assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Plugin.CrossFrame', ->
  CrossFrame = null
  fakeDiscovery = null
  fakeBridge = null
  fakeAnnotationSync = null
  sandbox = sinon.sandbox.create()

  createCrossFrame = (options) ->
    defaults =
      on: sandbox.stub()
      emit: sandbox.stub()
    element = document.createElement('div')
    return new Annotator.Plugin.CrossFrame(element, $.extend({}, defaults, options))

  beforeEach ->
    fakeDiscovery =
      startDiscovery: sandbox.stub()
      stopDiscovery: sandbox.stub()

    fakeBridge =
      createChannel: sandbox.stub()
      onConnect: sandbox.stub()
      notify: sandbox.stub()
      on: sandbox.stub()

    fakeAnnotationSync =
      sync: sandbox.stub()

    CrossFrame = Annotator.Plugin.CrossFrame
    sandbox.stub(CrossFrame, 'AnnotationSync').returns(fakeAnnotationSync)
    sandbox.stub(CrossFrame, 'Discovery').returns(fakeDiscovery)
    sandbox.stub(CrossFrame, 'Bridge').returns(fakeBridge)

  afterEach ->
    sandbox.restore()

  describe 'constructor', ->
    it 'instantiates the Discovery component', ->
      createCrossFrame()
      assert.called(CrossFrame.Discovery)
      assert.calledWith(CrossFrame.Discovery, window)

    it 'passes the options along to the bridge', ->
      createCrossFrame(server: true)
      assert.called(CrossFrame.Discovery)
      assert.calledWith(CrossFrame.Discovery, window, server: true)

    it 'instantiates the CrossFrame component', ->
      createCrossFrame()
      assert.called(CrossFrame.Bridge)
      assert.calledWith(CrossFrame.Discovery)

    it 'passes the options along to the bridge', ->
      createCrossFrame(scope: 'myscope')
      assert.called(CrossFrame.Bridge)
      assert.calledWith(CrossFrame.Bridge, scope: 'myscope')

    it 'instantiates the AnnotationSync component', ->
      createCrossFrame()
      assert.called(CrossFrame.AnnotationSync)

    it 'passes along options to AnnotationSync', ->
      formatter = (x) -> x
      createCrossFrame(formatter: formatter)
      assert.called(CrossFrame.AnnotationSync)
      assert.calledWith(CrossFrame.AnnotationSync, fakeBridge, {
        on: sinon.match.func
        emit: sinon.match.func
        formatter: formatter
      })

  describe '.pluginInit', ->
    it 'starts the discovery of new channels', ->
      bridge = createCrossFrame()
      bridge.pluginInit()
      assert.called(fakeDiscovery.startDiscovery)

    it 'creates a channel when a new frame is discovered', ->
      bridge = createCrossFrame()
      bridge.pluginInit()
      fakeDiscovery.startDiscovery.yield('SOURCE', 'ORIGIN', 'TOKEN')
      assert.called(fakeBridge.createChannel)
      assert.calledWith(fakeBridge.createChannel, 'SOURCE', 'ORIGIN', 'TOKEN')

  describe '.destroy', ->
    it 'stops the discovery of new frames', ->
      bridge = createCrossFrame()
      bridge.destroy()
      assert.called(fakeDiscovery.stopDiscovery)

  describe '.sync', ->
    it 'syncs the annotations with the other frame', ->
      bridge = createCrossFrame()
      bridge.sync()
      assert.called(fakeAnnotationSync.sync)

  describe '.on', ->
    it 'proxies the call to the bridge', ->
      bridge = createCrossFrame()
      bridge.on('event', 'arg')
      assert.calledWith(fakeBridge.on, 'event', 'arg')

  describe '.notify', ->
    it 'proxies the call to the bridge', ->
      bridge = createCrossFrame()
      bridge.notify(method: 'method')
      assert.calledWith(fakeBridge.notify, method: 'method')

  describe '.onConnect', ->
    it 'proxies the call to the bridge', ->
      bridge = createCrossFrame()
      fn = ->
      bridge.onConnect(fn)
      assert.calledWith(fakeBridge.onConnect, fn)
