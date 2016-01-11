{module, inject} = angular.mock
RPC = require('../frame-rpc')

describe 'Bridge', ->
  sandbox = sinon.sandbox.create()
  bridge = null
  createChannel = null
  fakeWindow = null

  before ->
    angular.module('h', [])
    .service('bridge', require('../bridge'))

  beforeEach module('h')
  beforeEach inject (_bridge_) ->
    bridge = _bridge_

    createChannel = ->
      bridge.createChannel(fakeWindow, 'http://example.com', 'TOKEN')

    fakeWindow = {
      postMessage: sandbox.stub()
    }

    sandbox.stub(window, 'addEventListener')
    sandbox.stub(window, 'removeEventListener')

  afterEach ->
    sandbox.restore()

  describe '.createChannel', ->
    it 'creates a new channel with the provided options', ->
      channel = createChannel()
      assert.equal(channel.src, window)
      assert.equal(channel.dst, fakeWindow)
      assert.equal(channel.origin, 'http://example.com')

    it 'adds the channel to the .links property', ->
      channel = createChannel()
      assert.include(bridge.links, {channel: channel, window: fakeWindow})

    it 'registers any existing listeners on the channel', ->
      message1 = sandbox.spy()
      message2 = sandbox.spy()
      bridge.on('message1', message1)
      bridge.on('message2', message2)
      channel = createChannel()
      assert.propertyVal(channel._methods, 'message1', message1)
      assert.propertyVal(channel._methods, 'message2', message2)

    it 'returns the newly created channel', ->
      channel = createChannel()
      assert.instanceOf(channel, RPC)

  describe '.call', ->
    it 'forwards the call to every created channel', ->
      channel = createChannel()
      sandbox.stub(channel, 'call')
      bridge.call('method1', 'params1')
      assert.called(channel.call)
      assert.calledWith(channel.call, 'method1', 'params1')

    it 'provides a timeout', (done) ->
      channel = createChannel()
      sandbox.stub(channel, 'call')
      sto = sandbox.stub(window, 'setTimeout').yields()
      bridge.call('method1', 'params1', done)

    it 'calls a callback when all channels return successfully', (done) ->
      channel1 = createChannel()
      channel2 = bridge.createChannel(fakeWindow, 'http://example.com', 'NEKOT')
      sandbox.stub(channel1, 'call').yields(null, 'result1')
      sandbox.stub(channel2, 'call').yields(null, 'result2')

      callback = (err, results) ->
        assert.isNull(err)
        assert.deepEqual(results, ['result1', 'result2'])
        done()

      bridge.call('method1', 'params1', callback)

    it 'calls a callback with an error when a channels fails', (done) ->
      error = new Error('Uh oh')
      channel1 = createChannel()
      channel2 = bridge.createChannel(fakeWindow, 'http://example.com', 'NEKOT')
      sandbox.stub(channel1, 'call').throws(error)
      sandbox.stub(channel2, 'call').yields(null, 'result2')

      callback = (err, results) ->
        assert.equal(err, error)
        done()

      bridge.call('method1', 'params1', callback)

    it 'destroys the channel when a call fails', (done) ->
      channel = createChannel()
      sandbox.stub(channel, 'call').throws(new Error(''))
      sandbox.stub(channel, 'destroy')

      callback = ->
        assert.called(channel.destroy)
        done()

      bridge.call('method1', 'params1', callback)

    it 'no longer publishes to a channel that has had an error', (done) ->
      channel = createChannel()
      sandbox.stub(channel, 'call').throws(new Error('oeunth'))
      bridge.call 'method1', 'params1', ->
        assert.calledOnce(channel.call)
        bridge.call 'method1', 'params1', ->
          assert.calledOnce(channel.call)
          done()

    it 'treats a timeout as a success with no result', (done) ->
      channel = createChannel()
      sandbox.stub(channel, 'call')
      sto = sandbox.stub(window, 'setTimeout').yields()
      bridge.call 'method1', 'params1', (err, res) ->
        assert.isNull(err)
        assert.deepEqual(res, [null])
        done()

    it 'returns a promise object', ->
      channel = createChannel()
      ret = bridge.call('method1', 'params1')
      assert.instanceOf(ret, Promise)

  describe '.on', ->
    it 'adds a method to the method registry', ->
      channel = createChannel()
      bridge.on('message1', sandbox.spy())
      assert.isFunction(bridge.channelListeners['message1'])

    it 'only allows registering a method once', ->
      bridge.on('message1', sandbox.spy())
      assert.throws ->
        bridge.on('message1', sandbox.spy())

  describe '.off', ->
    it 'removes the method from the method registry', ->
      channel = createChannel()
      bridge.on('message1', sandbox.spy())
      bridge.off('message1')
      assert.isUndefined(bridge.channelListeners['message1'])

  describe '.onConnect', ->
    it 'adds a callback that is called when a channel is connected', (done) ->
      callback = (c, s) ->
        assert.strictEqual(c, channel)
        assert.strictEqual(s, fakeWindow)
        done()

      data = {
        protocol: 'frame-rpc'
        method: 'connect'
        arguments: ['TOKEN']
      }

      event = {
        origin: 'http://example.com'
        data: data
      }

      addEventListener.yieldsAsync(event)
      bridge.onConnect(callback)
      channel = createChannel()

    it 'allows multiple callbacks to be registered', (done) ->
      callbackCount = 0
      callback = (c, s) ->
        assert.strictEqual(c, channel)
        assert.strictEqual(s, fakeWindow)
        if ++callbackCount is 2 then done()

      data = {
        protocol: 'frame-rpc'
        method: 'connect'
        arguments: ['TOKEN']
      }

      event = {
        origin: 'http://example.com'
        data: data
      }

      addEventListener.callsArgWithAsync(1, event)
      bridge.onConnect(callback)
      bridge.onConnect(callback)
      channel = createChannel()
