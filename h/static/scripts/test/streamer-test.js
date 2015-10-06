'use strict';

var streamer = require('../streamer');

function fakeSocketConstructor(url) {
  return {
    messages: [],
    onMessageCallbacks: [],
    didClose: false,

    send: function (message) {
      this.messages.push(message);
    },

    onMessage: function (callback) {
      this.onMessageCallbacks.push(callback);
    },

    notify: function (message) {
      this.onMessageCallbacks.forEach(function (callback) {
        callback({
          data: JSON.stringify(message)
        });
      });
    },

    close: function () {
      this.didClose = true
    }
  };
}

describe('streamer', function () {
  var fakeAnnotationMapper;
  var fakeGroups;
  var socket;

  beforeEach(function () {
    fakeAnnotationMapper = {
      loadAnnotations: sinon.stub(),
      unloadAnnotations: sinon.stub(),
    };

    fakeGroups = {
      focused: function () {
        return 'public';
      },
      add: sinon.stub(),
      remove: sinon.stub(),
    };

    socket = streamer.connect(
      fakeSocketConstructor,
      fakeAnnotationMapper,
      fakeGroups
    );
  });

  it('should send a client ID', function () {
    assert.equal(socket.messages.length, 1);
    assert.equal(socket.messages[0].messageType, 'client_id');
    assert.equal(socket.messages[0].value, streamer.clientId);
  });

  it('should close any existing socket', function () {
    var oldSocket = socket;
    var newSocket = streamer.connect(fakeSocketConstructor,
      fakeAnnotationMapper,
      fakeGroups
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

  describe('user status notifications', function () {
    it('adds a group on "group-joined" notifications', function () {
      socket.notify({
        type: 'user-status-notification',
        action: 'group-joined',
        group: {
          id: 'new-group'
        }
      });
      assert.ok(fakeGroups.add.calledOnce);
    });

    it('removes a group on "group-removed" notifications', function () {
      socket.notify({
        type: 'user-status-notification',
        action: 'group-left',
        group: {
          id: 'a-group'
        }
      });
      assert.ok(fakeGroups.remove.calledOnce);
    });
  });
});
