{module, inject} = angular.mock

describe 'Discovery', ->
  sandbox = sinon.sandbox.create()
  fakeTopWindow = null
  fakeFrameWindow = null
  createDiscovery = null

  before ->
    angular.module('h', [])
    .value('Discovery', require('../discovery'))

  beforeEach module('h')
  beforeEach inject (Discovery) ->
    createDiscovery = (win, options) ->
      new Discovery(win, options)

    createWindow = ->
      top: null
      addEventListener: sandbox.stub()
      removeEventListener: sandbox.stub()
      postMessage: sandbox.stub()
      length: 0
      frames: []

    fakeTopWindow = createWindow()
    fakeTopWindow.top = fakeTopWindow

    fakeFrameWindow = createWindow()
    fakeFrameWindow.top = fakeTopWindow

    fakeTopWindow.frames = [fakeFrameWindow]

  afterEach ->
    sandbox.restore()

  describe 'startDiscovery', ->
    it 'adds a "message" listener to the window object', ->
      discovery = createDiscovery(fakeTopWindow)
      discovery.startDiscovery(->)
      assert.called(fakeTopWindow.addEventListener)
      assert.calledWith(fakeTopWindow.addEventListener, 'message', sinon.match.func, false)

  describe 'when acting as a server (options.server = true)', ->
    server = null

    beforeEach ->
      server = createDiscovery(fakeFrameWindow, server: true)

    it 'sends out a "offer" message to every frame', ->
      server.startDiscovery(->)
      assert.called(fakeTopWindow.postMessage)
      assert.calledWith(fakeTopWindow.postMessage, '__cross_frame_dhcp_offer', '*')

    it 'allows the origin to be provided', ->
      server = createDiscovery(fakeFrameWindow, server: true, origin: 'foo')
      server.startDiscovery(->)
      assert.called(fakeTopWindow.postMessage)
      assert.calledWith(fakeTopWindow.postMessage, '__cross_frame_dhcp_offer', 'foo')

    it 'does not send the message to itself', ->
      server.startDiscovery(->)
      assert.notCalled(fakeFrameWindow.postMessage)

    it 'sends an "ack" on receiving a "request"', ->
      fakeFrameWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_request'
        source: fakeTopWindow
        origin: 'top'
      })
      server.startDiscovery(->)

      assert.called(fakeTopWindow.postMessage)
      matcher = sinon.match(/__cross_frame_dhcp_ack:\d+/)
      assert.calledWith(fakeTopWindow.postMessage, matcher, 'top')

    it 'sends an "ack" to the wildcard origin if a request comes from a frame with null origin', ->
      fakeFrameWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_request'
        source: fakeTopWindow
        origin: 'null'
      })
      server.startDiscovery(->)

      assert.called(fakeTopWindow.postMessage)
      matcher = sinon.match(/__cross_frame_dhcp_ack:\d+/)
      assert.calledWith(fakeTopWindow.postMessage, matcher, '*')

    it 'calls the discovery callback on receiving "request"', ->
      fakeFrameWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_request'
        source: fakeTopWindow
        origin: 'top'
      })
      handler = sandbox.stub()
      server.startDiscovery(handler)
      assert.called(handler)
      assert.calledWith(handler, fakeTopWindow, 'top', sinon.match(/\d+/))

    it 'raises an error if it recieves an event from another server', ->
      fakeFrameWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeTopWindow
        origin: 'top'
      })
      handler = sandbox.stub()
      assert.throws ->
        server.startDiscovery(handler)

  describe 'when acting as a client (options.client = false)', ->
    client = null

    beforeEach ->
      client = createDiscovery(fakeTopWindow)

    it 'sends out a discovery message to every frame', ->
      client.startDiscovery(->)
      assert.called(fakeFrameWindow.postMessage)
      assert.calledWith(fakeFrameWindow.postMessage, '__cross_frame_dhcp_discovery', '*')

    it 'does not send the message to itself', ->
      client.startDiscovery(->)
      assert.notCalled(fakeTopWindow.postMessage)

    it 'sends a "request" in response to an "offer"', ->
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeFrameWindow
        origin: 'iframe'
      })
      client.startDiscovery(->)

      assert.called(fakeFrameWindow.postMessage)
      assert.calledWith(fakeFrameWindow.postMessage, '__cross_frame_dhcp_request', 'iframe')

    it 'does not respond to an "offer" if a "request" is already in progress', ->
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeFrameWindow
        origin: 'iframe1'
      })
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeFrameWindow
        origin: 'iframe2'
      })
      client.startDiscovery(->)

      # Twice, once for discovery, once for offer.
      assert.calledTwice(fakeFrameWindow.postMessage)
      lastCall = fakeFrameWindow.postMessage.lastCall
      assert(lastCall.notCalledWith(sinon.match.string, 'iframe2'))

    it 'allows responding to a "request" once a previous "request" has completed', ->
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeFrameWindow
        origin: 'iframe1'
      })
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_ack:1234'
        source: fakeFrameWindow
        origin: 'iframe1'
      })
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_offer'
        source: fakeFrameWindow
        origin: 'iframe2'
      })
      client.startDiscovery(->)

      assert.called(fakeFrameWindow.postMessage)
      assert.calledWith(fakeFrameWindow.postMessage, '__cross_frame_dhcp_request', 'iframe2')

    it 'calls the discovery callback on receiving an "ack"', ->
      fakeTopWindow.addEventListener.yields({
        data: '__cross_frame_dhcp_ack:1234'
        source: fakeFrameWindow
        origin: 'iframe'
      })
      callback = sandbox.stub()
      client.startDiscovery(callback)

      assert.called(callback)
      assert.calledWith(callback, fakeFrameWindow, 'iframe', '1234')

  describe 'stopDiscovery', ->
    it 'removes the "message" listener from the window', ->
      discovery = createDiscovery(fakeFrameWindow)
      discovery.startDiscovery()
      discovery.stopDiscovery()

      handler = fakeFrameWindow.addEventListener.lastCall.args[1]
      assert.called(fakeFrameWindow.removeEventListener)
      assert.calledWith(fakeFrameWindow.removeEventListener, 'message', handler)

    it 'allows startDiscovery to be called with a new handler', ->
      discovery = createDiscovery(fakeFrameWindow)
      discovery.startDiscovery()
      discovery.stopDiscovery()

      assert.doesNotThrow ->
        discovery.startDiscovery()
