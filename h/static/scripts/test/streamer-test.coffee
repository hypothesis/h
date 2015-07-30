{module, inject} = angular.mock

describe 'streamer', ->
  WebSocket = null
  fakeSock = null
  streamer = null
  url = 'wss://magicstreemz/giraffe'
  sandbox = null

  before ->
    angular.module('h', [])
    .service('streamer', require('../streamer'))

  beforeEach module('h')

  beforeEach module ->
    sandbox = sinon.sandbox.create()
    fakeSock = {
      send: sandbox.spy()
      close: sandbox.spy()
    }
    WebSocket = sandbox.stub().returns(fakeSock)
    return

  beforeEach inject (_streamer_) ->
    streamer = _streamer_
    streamer.clientId = 'FAKE_CLIENT_ID'

  afterEach ->
    sandbox.restore()

  it 'calls the transport function with the new keyword', ->
    streamer.open(WebSocket, url)

    assert.calledWithNew(WebSocket)

  it 'creates a socket with the correct base URL', ->
    streamer.open(WebSocket, url)

    assert.calledWith(WebSocket, 'wss://magicstreemz/giraffe')

  it 'does not open another socket while connecting or connected', ->
    streamer.open(WebSocket, url)
    streamer.open(WebSocket, url)

    assert.calledOnce(WebSocket)

    fakeSock.onopen()
    streamer.open(WebSocket, url)

    assert.calledOnce(WebSocket)

  it 'does not close the socket again when already closing', ->
    streamer.open(WebSocket, url)
    streamer.close()
    streamer.close()

    assert.calledOnce(fakeSock.close)

  it 'queues messages kuntil the socket is open', ->
    streamer.open(WebSocket, url)
    streamer.send({animal: 'elephant'})

    assert.notCalled(fakeSock.send)

    fakeSock.onopen()

    assert.called(fakeSock.send)

  it 'calls the onopen handler once the socket is open', ->
    streamer.onopen = sinon.spy()
    streamer.open(WebSocket, url)

    assert.notCalled(streamer.onopen)

    fakeSock.onopen()

    assert.called(streamer.onopen)

  it 'preserves message ordering in the queue', ->
    streamer.open(WebSocket, url)
    streamer.send({animal: 'elephant'})
    streamer.send({animal: 'giraffe'})
    fakeSock.onopen()

    firstAnimal = JSON.parse(fakeSock.send.getCall(1).args[0]).animal
    secondAnimal = JSON.parse(fakeSock.send.getCall(2).args[0]).animal
    assert.equal(firstAnimal, 'elephant')
    assert.equal(secondAnimal, 'giraffe')

  it 'converts message data to JSON', ->
    streamer.open(WebSocket, url)
    streamer.send({animal: 'badger'})
    fakeSock.onopen()

    assert.calledWith(fakeSock.send, JSON.stringify({animal: 'badger'}))

  it 'sends a client ID as the first message once the socket opens', ->
    streamer.send({animal: 'elephant'})
    streamer.open(WebSocket, url)
    fakeSock.onopen()

    msg = fakeSock.send.getCall(0).args[0]
    data = JSON.parse(msg)

    assert.equal(data.messageType, 'client_id')
    assert.equal(typeof data.value, 'string')

  it 'attempts to reopen the socket on connection failure', ->
    clock = sandbox.useFakeTimers()

    streamer.open(WebSocket, url)
    fakeSock.onclose()

    clock.tick(500)

    assert.calledTwice(WebSocket)
    assert.match(WebSocket.getCall(0).args, WebSocket.getCall(1).args)

  it 'closes the socket when close is called', ->
    streamer.open(WebSocket, url)
    streamer.close()

    assert.calledOnce(fakeSock.close)

  it 'only closes the socket once', ->
    streamer.open(WebSocket, url)
    streamer.close()
    streamer.close()

    assert.calledOnce(fakeSock.close)

  it 'does not try and reopen the socket when closed explicitly', ->
    clock = sandbox.useFakeTimers()
    streamer.open(WebSocket, url)
    streamer.close()
    fakeSock.onclose()

    clock.tick(500)
    assert.calledOnce(WebSocket)

  it 'calls the onmessage handler when the socket receives a message', ->
    streamer.onmessage = sinon.spy()
    streamer.open(WebSocket, url)
    fakeSock.onmessage(data: JSON.stringify({animal: 'baboon'}))
    assert.called(streamer.onmessage)

  it 'calls the onmessage handler with parsed JSON', ->
    streamer.onmessage = sinon.spy()
    streamer.open(WebSocket, url)
    fakeSock.onmessage(data: JSON.stringify({animal: 'baboon'}))
    assert.calledWith(streamer.onmessage, {animal: 'baboon'})
