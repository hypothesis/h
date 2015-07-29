{module, inject} = require('angular-mock')

describe 'CrossFrame', ->
  sandbox = sinon.sandbox.create()
  crossframe = null
  $rootScope = null
  $fakeDocument = null
  $fakeWindow = null
  fakeStore = null
  fakeAnnotationUI = null
  fakeDiscovery = null
  fakeBridge = null
  fakeAnnotationSync = null
  fakeAnnotationUISync = null

  before ->
    angular.module('h', [])
    .service('crossframe', require('../cross-frame'))

  beforeEach module('h')
  beforeEach module ($provide) ->
    $fakeDocument = {}
    $fakeWindow = {}
    fakeStore = {}
    fakeAnnotationUI = {}
    fakeDiscovery =
      startDiscovery: sandbox.stub()
    fakeBridge =
      notify: sandbox.stub()
      createChannel: sandbox.stub()
      onConnect: sandbox.stub()
    fakeAnnotationSync = {}
    fakeAnnotationUISync = {}

    $provide.value('$document', $fakeDocument)
    $provide.value('$window', $fakeWindow)
    $provide.value('store', fakeStore)
    $provide.value('annotationUI', fakeAnnotationUI)
    $provide.value('Discovery',
      sandbox.stub().returns(fakeDiscovery))
    $provide.value('bridge', fakeBridge)
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
      fakeDiscovery.startDiscovery.yields('source', 'origin', 'token')
      crossframe.connect()
      assert.calledWith(fakeBridge.createChannel,
        'source', 'origin', 'token')

    it 'queries discovered frames for metadata', ->
      uri = 'http://example.com'
      channel = {call: sandbox.stub().yieldsTo('success', {uri: uri})}
      fakeBridge.onConnect.yields(channel)
      crossframe.connect()
      assert.calledWith(channel.call, {
        method: 'getDocumentInfo'
        success: sinon.match.func
      })

    it 'updates the frames array', ->
      uri = 'http://example.com'
      channel = {call: sandbox.stub().yieldsTo('success', {uri: uri})}
      fakeBridge.onConnect.yields(channel)
      crossframe.connect()
      assert.deepEqual(crossframe.frames, [
        {channel: channel, uri: uri}
      ])


  describe '.notify()', ->
    it 'proxies the call to the bridge', ->
      message = {method: 'foo', params: 'bar'}
      crossframe.connect() # create the bridge.
      crossframe.notify(message)
      assert.calledOn(fakeBridge.notify, fakeBridge)
      assert.calledWith(fakeBridge.notify, message)
