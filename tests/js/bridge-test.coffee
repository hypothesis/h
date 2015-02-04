assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'Bridge', ->
  sandbox = sinon.sandbox.create()
  createBridge = null
  createChannel = null

  beforeEach module('h')
  beforeEach inject (Bridge) ->
    createBridge = (options) ->
      new Bridge(options)

    createChannel = ->
      call: sandbox.stub()
      bind: sandbox.stub()
      unbind: sandbox.stub()
      notify: sandbox.stub()
      destroy: sandbox.stub()

    sandbox.stub(Channel, 'build')

  afterEach ->
    sandbox.restore()

  describe '.createChannel', ->
    it 'creates a new channel with the provided options', ->
      Channel.build.returns(createChannel())
      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.called(Channel.build)
      assert.calledWith(Channel.build, {
        window: 'WINDOW'
        origin: 'ORIGIN'
        scope: 'bridge:TOKEN'
        onReady: sinon.match.func
      })

    it 'adds the channel to the .links property', ->
      channel = createChannel()
      Channel.build.returns(channel)
      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.include(bridge.links, {channel: channel, window: 'WINDOW'})

    it 'registers any existing listeners on the channel', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.on('message1', sinon.spy())
      bridge.on('message2', sinon.spy())
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.called(channel.bind)
      assert.calledWith(channel.bind, 'message1', sinon.match.func)
      assert.calledWith(channel.bind, 'message2', sinon.match.func)

    it 'returns the newly created channel', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      ret = bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.equal(ret, channel)

  describe '.call', ->
    it 'forwards the call to every created channel', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.call({method: 'method1', params: 'params1'})

      assert.called(channel.call)
      message = channel.call.lastCall.args[0]
      assert.equal(message.method, 'method1')
      assert.equal(message.params, 'params1')

    it 'provides a timeout', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.call({method: 'method1', params: 'params1'})

      message = channel.call.lastCall.args[0]
      assert.isNumber(message.timeout)

    it 'calls options.callback when all channels return successfully', ->
      channel1 = createChannel()
      channel2 = createChannel()
      channel1.call.yieldsTo('success', 'result1')
      channel2.call.yieldsTo('success', 'result2')

      callback = sandbox.stub()

      bridge = createBridge()
      Channel.build.returns(channel1)
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      Channel.build.returns(channel2)
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      bridge.call({method: 'method1', params: 'params1', callback: callback})

      assert.called(callback)
      assert.calledWith(callback, null, ['result1', 'result2'])

    it 'calls options.callback with an error when one or more channels fail', ->
      err = new Error('Uh oh')
      channel1 = createChannel()
      channel1.call.yieldsTo('error', err, 'A reason for the error')
      channel2 = createChannel()
      channel2.call.yieldsTo('success', 'result2')

      callback = sandbox.stub()
      bridge = createBridge()

      Channel.build.returns(channel1)
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      Channel.build.returns(channel2)
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      bridge.call({method: 'method1', params: 'params1', callback: callback})

      assert.called(callback)
      assert.calledWith(callback, err)

    it 'destroys the channel when a call fails', ->
      channel = createChannel()
      channel.call.yieldsTo('error', new Error(''), 'A reason for the error')
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.call({method: 'method1', params: 'params1', callback: sandbox.stub()})

      assert.called(channel.destroy)

    it 'no longer publishes to a channel that has had an errored response', ->
      channel = createChannel()
      channel.call.yieldsTo('error', new Error(''), 'A reason for the error')
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.call({method: 'method1', params: 'params1', callback: sandbox.stub()})
      bridge.call({method: 'method1', params: 'params1', callback: sandbox.stub()})

      assert.calledOnce(channel.call)

    it 'treats a timeout as a success with no result', ->
      channel = createChannel()
      channel.call.yieldsTo('error', 'timeout_error', 'timeout')
      Channel.build.returns(channel)

      callback = sandbox.stub()
      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.call({method: 'method1', params: 'params1', callback: callback})

      assert.called(callback)
      assert.calledWith(callback, null, [null])

    it 'returns a promise object', ->
      channel = createChannel()
      channel.call.yieldsTo('error', 'timeout_error', 'timeout')
      Channel.build.returns(channel)

      bridge = createBridge()
      ret = bridge.call({method: 'method1', params: 'params1'})
      assert.isFunction(ret.then)

  describe '.notify', ->
    it 'publishes the message on every created channel', ->
      channel = createChannel()
      message = {method: 'message1', params: 'params'}
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.notify(message)

      assert.called(channel.notify)
      assert.calledWith(channel.notify, message)

  describe '.on', ->
    it 'registers an event listener on all created channels', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.on('message1', sandbox.spy())

      assert.called(channel.bind)
      assert.calledWith(channel.bind, 'message1', sinon.match.func)

    it 'only allows one message to be registered per method', ->
      bridge = createBridge()
      bridge.on('message1', sandbox.spy())
      assert.throws ->
        bridge.on('message1', sandbox.spy())

  describe '.off', ->
    it 'removes the event listener from the created channels', ->
      channel = createChannel()
      Channel.build.returns(channel)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.off('message1', sandbox.spy())

    it 'ensures that the event is no longer bound when new channels are created', ->
      channel1 = createChannel()
      channel2 = createChannel()
      Channel.build.returns(channel1)

      bridge = createBridge()
      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      bridge.off('message1', sandbox.spy())

      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')
      assert.notCalled(channel2.bind)

  describe '.onConnect', ->
    it 'adds a callback that is called when a new channel is connected', ->
      channel = createChannel()
      Channel.build.returns(channel)
      Channel.build.yieldsTo('onReady', channel)

      callback = sandbox.stub()
      bridge = createBridge()
      bridge.onConnect(callback)

      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.called(callback)
      assert.calledWith(callback, channel)

    it 'allows multiple callbacks to be registered', ->
      channel = createChannel()
      Channel.build.returns(channel)
      Channel.build.yieldsTo('onReady', channel)

      callback1 = sandbox.stub()
      callback2 = sandbox.stub()
      bridge = createBridge()
      bridge.onConnect(callback1)
      bridge.onConnect(callback2)

      bridge.createChannel('WINDOW', 'ORIGIN', 'TOKEN')

      assert.called(callback1)
      assert.called(callback2)

