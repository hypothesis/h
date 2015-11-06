'use strict';

var EventEmitter = require('events');
var util = require('util');

var proxyquire = require('proxyquire');

function FakeSocket(url) {
  this.messages = [];
  this.didClose = false;

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
    assert.equal(socket.messages.length, 1);
    assert.equal(socket.messages[0].messageType, 'client_id');
    assert.equal(socket.messages[0].value, streamer.clientId);
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
    assert.ok(oldSocket.didClose);
    assert.ok(!newSocket.didClose);
  });

  describe('annotation notifications', function () {
    it('should load new annotations', function () {
      socket.notify({
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
      socket.notify({
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
      socket.notify({
        type: 'session-change',
        model: model,
      });
      assert.ok(fakeSession.update.calledWith(model));
    });
  });
});
