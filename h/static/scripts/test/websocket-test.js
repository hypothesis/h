var Socket = require('../websocket');

describe('websocket wrapper', function () {
  var fakeSocket;
  var clock;

  function FakeWebSocket() {
    this.close = sinon.stub();
    this.send = sinon.stub();
    fakeSocket = this;
  };
  FakeWebSocket.OPEN = 1;

  var WebSocket = window.WebSocket;

  beforeEach(function () {
    global.WebSocket = FakeWebSocket;
    clock = sinon.useFakeTimers();
  });

  afterEach(function () {
    global.WebSocket = WebSocket;
    clock.restore();
  });

  it('should reconnect after an abnormal disconnection', function () {
    var socket = new Socket('ws://test:1234');
    assert.ok(fakeSocket);
    var initialSocket = fakeSocket;
    fakeSocket.onclose({code: 1006});
    clock.tick(1000);
    assert.ok(fakeSocket);
    assert.notEqual(fakeSocket, initialSocket);
  });

  it('should send queued messages after a reconnect', function () {
    // simulate WebSocket setup and initial connection
    var socket = new Socket('ws://test:1234');
    fakeSocket.onopen({});

    // simulate abnormal disconnection
    fakeSocket.onclose({code: 1006});

    // enqueue a message and check that it is sent after the WS reconnects
    socket.send({aKey: 'aValue'});
    fakeSocket.onopen({});
    assert.calledWith(fakeSocket.send, '{"aKey":"aValue"}');
  });

  it('should not reconnect after a normal disconnection', function () {
    var socket = new Socket('ws://test:1234');
    socket.close();
    assert.called(fakeSocket.close);
    var initialSocket = fakeSocket;
    clock.tick(1000);
    assert.equal(fakeSocket, initialSocket);
  });

  it('should queue messages sent prior to connection', function () {
    var socket = new Socket('ws://test:1234');
    socket.send({abc: 'foo'});
    assert.notCalled(fakeSocket.send);
    fakeSocket.onopen({});
    assert.calledWith(fakeSocket.send, '{"abc":"foo"}');
  });

  it('should send messages immediately when connected', function () {
    var socket = new Socket('ws://test:1234');
    fakeSocket.readyState = FakeWebSocket.OPEN;
    socket.send({abc: 'foo'});
    assert.calledWith(fakeSocket.send, '{"abc":"foo"}');
  });
});
