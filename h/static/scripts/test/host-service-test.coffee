{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null

describe 'Host service', ->
  sandbox = null
  host = null
  createChannel = -> notify: sandbox.stub()
  fakeBridge = null
  $digest = null
  publish = null
  PARENT_WINDOW = 'PARENT_WINDOW'
  dumpListeners = null

  before ->
    require('../host-service')

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()
    fakeWindow = parent: PARENT_WINDOW

    listeners = {}

    publish = ({method, params}) ->
      listeners[method]('ctx', params)

    fakeBridge =
      ls: listeners
      on: sandbox.spy (method, fn) -> listeners[method] = fn
      notify: sandbox.stub()
      onConnect: sandbox.stub()
      links: [
        {window: PARENT_WINDOW,    channel: createChannel()}
        {window: 'ANOTHER_WINDOW', channel: createChannel()}
        {window: 'THIRD_WINDOW',   channel: createChannel()}
      ]

    $provide.value 'bridge', fakeBridge
    $provide.value '$window', fakeWindow

    return

  afterEach ->
    sandbox.restore()

  beforeEach inject ($rootScope, _host_) ->
    host = _host_
    $digest = sandbox.stub($rootScope, '$digest')

  describe 'on "back" event', ->
    it 'sends the "hideFrame" message to the host only', ->
      publish({method: 'back'})
      assert.calledWith(fakeBridge.links[0].channel.notify, method: 'hideFrame')
      assert.notCalled(fakeBridge.links[1].channel.notify)
      assert.notCalled(fakeBridge.links[2].channel.notify)

  describe 'on "open" event', ->
    it 'sends the "showFrame" message to the host only', ->
      publish({method: 'open'})
      assert.calledWith(fakeBridge.links[0].channel.notify, method: 'showFrame')
      assert.notCalled(fakeBridge.links[1].channel.notify)
      assert.notCalled(fakeBridge.links[2].channel.notify)
