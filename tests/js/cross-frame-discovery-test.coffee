assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'CrossFrameDiscovery', ->
  sandbox = sinon.sandbox.create()
  fakeWindow = null
  createDiscovery = null

  beforeEach module('h')
  beforeEach inject (CrossFrameDiscovery) ->
    fakeWindow = {
      top: null
      addEventListener: sandbox.stub()
      removeEventListener: sandbox.stub()
    }
    createBridge = (options) ->
      new CrossFrameDiscovery(fakeWindow, options)

  afterEach ->
    sandbox.restore()

  describe 'startDiscovery', ->
    it 'adds a "message" listener to the window object'

    describe 'when acting as a server (options.server = true)', ->
      it 'sends out a "discovery" message to every frame'
      it 'does not send the message to itself'
      it 'sends an "ack" on receiving a "request"'
      it 'calls the discovery callback on receiving "request"'

    describe 'when acting as a client (options.client = false)', ->
      it 'sends out a discovery message to every frame'
      it 'does not send the message to itself'
      it 'sends a "request" in response to an "offer"'
      it 'does not respond to an "offer" if a "request" is already in progress'
      it 'allows responding to a "request" once a previous "request" has completed'
      it 'calls the discovery callback on receiving an "ack"'

  describe 'stopDiscovery', ->
    it 'removes the "message" listener from the window'
    it 'allows startDiscovery to be called with a new handler'
