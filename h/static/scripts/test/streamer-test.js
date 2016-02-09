'use strict';

var inherits = require('inherits');
var EventEmitter = require('tiny-emitter');

var proxyquire = require('proxyquire');

// the most recently created FakeSocket instance
var fakeWebSocket = null;

function FakeSocket(url) {
  fakeWebSocket = this;

  this.messages = [];
  this.didClose = false;

  this.isConnected = sinon.stub().returns(true);

  this.send = function (message) {
    this.messages.push(message);
  };

  this.notify = function (message) {
    this.emit('message', {data: JSON.stringify(message)});
  };

  this.close = function () {
    this.didClose = true
  };
}
inherits(FakeSocket, EventEmitter);

describe('streamer', function () {
  var fakeAnnotationMapper;
  var fakeGroups;
  var fakeRootScope;
  var fakeSession;
  var fakeSettings;
  var activeStreamer;
  var streamer;

  function createDefaultStreamer() {
    activeStreamer = streamer.connect(
      fakeRootScope,
      fakeAnnotationMapper,
      fakeGroups,
      fakeSession,
      fakeSettings
    );
  }

  beforeEach(function () {
    fakeRootScope = {
      $apply: function (callback) {
        callback();
      }
    };

    fakeAnnotationMapper = {
      loadAnnotations: sinon.stub(),
      unloadAnnotations: sinon.stub(),
    };

    fakeGroups = {
      focused: function () {
        return 'public';
      },
    };

    fakeSession = {
      update: sinon.stub(),
    };

    fakeSettings = {
      websocketUrl: 'ws://example.com/ws',
    };

    streamer = proxyquire('../streamer', {
      './websocket': FakeSocket,
    });
  });

  it('should not create a websocket connection if websocketUrl is not provided', function () {
    fakeSettings = {}
    createDefaultStreamer();
    assert.isNull(fakeWebSocket);
  });

  it('should send a client ID', function () {
    createDefaultStreamer();
    assert.equal(fakeWebSocket.messages.length, 1);
    assert.equal(fakeWebSocket.messages[0].messageType, 'client_id');
    assert.equal(fakeWebSocket.messages[0].value, streamer.clientId);
  });

  it('should close any existing socket', function () {
    createDefaultStreamer();
    var oldStreamer = activeStreamer;
    var oldWebSocket = fakeWebSocket;
    var newStreamer = streamer.connect(
      fakeRootScope,
      fakeAnnotationMapper,
      fakeGroups,
      fakeSession,
      fakeSettings
    );
    assert.ok(oldWebSocket.didClose);
    assert.ok(!fakeWebSocket.didClose);
  });

  describe('annotation notifications', function () {
    it('should load new annotations', function () {
      createDefaultStreamer();
      fakeWebSocket.notify({
        type: 'annotation-notification',
        options: {
          action: 'create',
        },
        payload: [{
          group: 'public'
        }]
      });
      assert.ok(fakeAnnotationMapper.loadAnnotations.calledOnce);
    });

    it('should unload deleted annotations', function () {
      createDefaultStreamer();
      fakeWebSocket.notify({
        type: 'annotation-notification',
        options: {
          action: 'delete',
        },
        payload: [{
          group: 'public'
        }]
      });
      assert.ok(fakeAnnotationMapper.unloadAnnotations.calledOnce);
    });
  });

  describe('session change notifications', function () {
    it('updates the session when a notification is received', function () {
      createDefaultStreamer();
      var model = {
        groups: [{
          id: 'new-group'
        }]
      };
      fakeWebSocket.notify({
        type: 'session-change',
        model: model,
      });
      assert.ok(fakeSession.update.calledWith(model));
    });
  });

  describe('reconnections', function () {
    it('resends configuration messages when a reconnection occurs', function () {
      createDefaultStreamer();
      fakeWebSocket.messages = [];
      fakeWebSocket.emit('open');
      assert.equal(fakeWebSocket.messages.length, 1);
      assert.equal(fakeWebSocket.messages[0].messageType, 'client_id');
    });
  });
});
