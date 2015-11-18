'use strict';

var retry = require('retry');
var EventEmitter = require('tiny-emitter');
var inherits = require('inherits');

// see https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent
var CLOSE_NORMAL = 1000;

/**
 * Socket is a minimal wrapper around WebSocket which provides:
 *
 * - Automatic reconnection in the event of an abnormal close
 * - Queuing of messages passed to send() whilst the socket is
 *   connecting
 * - Uses the standard EventEmitter API for reporting open, close, error
 *   and message events.
 */
function Socket(url) {
  var self = this;

  // queue of JSON objects which have not yet been submitted
  var messageQueue = [];

  // the current WebSocket instance or null if disconnected
  var socket;

  function sendMessages() {
    while (messageQueue.length > 0) {
      var messageString = JSON.stringify(messageQueue.shift());
      socket.send(messageString);
    }
  }

  function reconnect() {
    var didConnect = false;
    var connectOperation = retry.operation();
    connectOperation.attempt(function (currentAttempt) {
      socket = new WebSocket(url);
      socket.onopen = function (event) {
        // signal successful connection
        connectOperation.retry();
        didConnect = true;
        sendMessages();

        self.emit('open', event);
      };

      socket.onclose = function (event) {
        if (event.code !== CLOSE_NORMAL) {
          if (didConnect) {
            console.warn('The WebSocket connection closed abnormally ' +
              '(code: %d, reason: %s). Reconnecting automatically.',
              event.code, event.reason);
            reconnect();
          } else {
            console.warn('Retrying connection (attempt %d)', currentAttempt);
            connectOperation.retry(new Error(event.reason));
          }
        }
        socket = null;
        self.emit('close', event);
      };

      socket.onerror = function (event) {
        self.emit('error', event);
      };

      socket.onmessage = function (event) {
        self.emit('message', event);
      };
    });
  };

  /** Close the underlying WebSocket connection */
  this.close = function () {
    if (!socket) {
      console.error('Socket.close() called before socket was connected');
      return;
    }
    socket.close();
  };

  /**
   * Send a JSON object via the WebSocket connection, or queue it
   * for later delivery if not currently connected.
   */
  this.send = function (message) {
    messageQueue.push(message);
    if (this.isConnected()) {
      sendMessages();
    }
  };

  /** Returns true if the WebSocket is currently connected. */
  this.isConnected = function () {
    return socket && socket.readyState === WebSocket.OPEN;
  };

  // establish the initial connection
  reconnect();
}

inherits(Socket, EventEmitter);

module.exports = Socket;
