assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'CrossFrameBridge', ->
  sandbox = sinon.sandbox.create()
  createBridge = null
  createChannel = null

  beforeEach module('h')
  beforeEach module (CrossFrameBridge) ->
    createBridge = (options) ->
      new CrossFrameBridge(options)

    createChannel ->
      call: sandbox.stub()
      bind: sandbox.stub()
      unbind: sandbox.stub()
      notify: sandbox.stub()

  afterEach ->
    sandbox.restore()

  describe '.createChannel', ->
    it 'creates a new channel with the provided options'
    it 'adds the channel to the .links property'
    it 'registers any channelListeners on the channel'
    it 'returns the newly created channel'

  describe '.call', ->
    it 'forwards the call to every created channel'
    it 'provides a timeout of 1000ms'
    it 'calls options.callback when all channels return successfully'
    it 'calls options.callback with an error when one or more channels fail'
    it 'destroys the channel when a call fails'
    it 'removes the channel from the .links array when a call fails'
    it 'treats a timeout as a success with no result'
    it 'returns a promise object'

  describe '.notify', ->
    it 'publishes the message on every created channel'

  describe '.on', ->
    it 'registers an event listener on all created channels'
    it 'adds the message to the .channelListeners property'
    it 'only allows one message to be registered per method'

  describe '.off', ->
    it 'removes the event listener from the created channels'
    it 'removes the method from th .channelListeners property'

  describe '.onConnect', ->
    it 'adds a callback that is called when a new channel is connected'
    it 'allows multiple callbacks to be registered'
