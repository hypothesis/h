assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'CrossFrameService', ->
  sandbox = sinon.sandbox.create()
  crossframe = null
  $rootScope = null
  $fakeDocument = null
  $fakeWindow = null
  fakeStore = null
  fakeAnnotationUI = null
  fakeCrossFrameDiscovery = null
  fakeCrossFrameBridge = null
  fakeAnnotationSync = null
  fakeAnnotationUISync = null

  beforeEach module('h')
  beforeEach module ($provide) ->
    $fakeDocument = {}
    $fakeWindow = {}
    fakeStore = {}
    fakeAnnotationUI = {}
    fakeCrossFrameDiscovery =
      startDiscovery: sandbox.stub()
    fakeCrossFrameBridge =
      notify: sandbox.stub()
      createChannel: sandbox.stub()
      onConnect: sandbox.stub()
    fakeAnnotationSync = {}
    fakeAnnotationUISync = {}

    $provide.value('$document', $fakeDocument)
    $provide.value('$window', $fakeWindow)
    $provide.value('store', fakeStore)
    $provide.value('annotationUI', fakeAnnotationUI)
    $provide.value('CrossFrameDiscovery',
      sandbox.stub().returns(fakeCrossFrameDiscovery))
    $provide.value('CrossFrameBridge',
      sandbox.stub().returns(fakeCrossFrameBridge))
    $provide.value('AnnotationSync',
      sandbox.stub().returns(fakeAnnotationSync))
    $provide.value('AnnotationUISync',
      sandbox.stub().returns(fakeAnnotationUISync))
    return # $provide returns a promise.

  beforeEach inject (_$rootScope_, _crossframe_) ->
    $rootScope = _$rootScope_
    crossframe = _crossframe_

  afterEach ->
    sandbox.restore()

  describe '.connect()', ->
    it 'creates a new channel when the discovery module finds a frame', ->
      fakeCrossFrameDiscovery.startDiscovery.yields('source', 'origin', 'token')
      crossframe.connect()
      assert.calledWith(fakeCrossFrameBridge.createChannel,
        'source', 'origin', 'token')

    it 'queries discovered frames for metadata', ->
      info = {metadata: link: [{href: 'http://example.com'}]}
      channel = {call: sandbox.stub().yieldsTo('success', info)}
      fakeCrossFrameBridge.onConnect.yields(channel)
      crossframe.connect()
      assert.calledWith(channel.call, {
        method: 'getDocumentInfo'
        success: sinon.match.func
      })

    it 'updates the providers array', ->
      info = {metadata: link: [{href: 'http://example.com'}]}
      channel = {call: sandbox.stub().yieldsTo('success', info)}
      fakeCrossFrameBridge.onConnect.yields(channel)
      crossframe.connect()
      assert.deepEqual(crossframe.providers, [
        {channel: channel, entities: ['http://example.com']}
      ])


  describe '.notify()', ->
    it 'proxies the call to the bridge', ->
      message = {method: 'foo', params: 'bar'}
      crossframe.connect() # create the bridge.
      crossframe.notify(message)
      assert.calledOn(fakeCrossFrameBridge.notify, fakeCrossFrameBridge)
      assert.calledWith(fakeCrossFrameBridge.notify, message)
