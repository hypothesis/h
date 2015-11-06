'use strict';

var EventEmitter = require('events');
var util = require('util');

var proxyquire = require('proxyquire');

function FakeSocket(url) {
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
util.inherits(FakeSocket, EventEmitter);

describe('streamer', function () {
  var fakeAnnotationMapper;
  var fakeGroups;
  var fakeSession;
  var fakeSettings;
  var socket;
  var streamer;

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

    socket = streamer.connect(
      fakeRootScope,
      fakeAnnotationMapper,
      fakeGroups,
      fakeSession,
      fakeSettings
    );
  });

  it('should send a client ID', function () {
    var fakeWebSocket = socket._socket;
    assert.equal(fakeWebSocket.messages.length, 1);
    assert.equal(fakeWebSocket.messages[0].messageType, 'client_id');
    assert.equal(fakeWebSocket.messages[0].value, streamer.clientId);
  });

  it('should close any existing socket', function () {
    var oldSocket = socket;
    var newSocket = streamer.connect(
      fakeRootScope,
      fakeAnnotationMapper,
      fakeGroups,
      fakeSession,
      fakeSettings
    );
    assert.ok(oldSocket._socket.didClose);
    assert.ok(!newSocket._socket.didClose);
  });

  describe('annotation notifications', function () {
    it('should load new annotations', function () {
      socket._socket.notify({
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
      socket._socket.notify({
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
      var model = {
        groups: [{
          id: 'new-group'
        }]
      };
      socket._socket.notify({
        type: 'session-change',
        model: model,
      });
      assert.ok(fakeSession.update.calledWith(model));
    });
  });

  describe('reconnections', function () {
    it('resends configuration messages when a reconnection occurs', function () {
      var fakeWebSocket = socket._socket;
      fakeWebSocket.messages = [];
      fakeWebSocket.emit('open');
      assert.equal(fakeWebSocket.messages.length, 1);
      assert.equal(fakeWebSocket.messages[0].messageType, 'client_id');
    });
  });
});
