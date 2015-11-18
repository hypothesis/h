var uuid = require('node-uuid')

var Socket = require('./websocket');

// the randomly generated session UUID
var clientId = uuid.v4();

// the singleton socket instance, only one may
// be open at a time
var socket;

/**
 * Open a new WebSocket connection to the Hypothesis push notification service.
 * Only one websocket connection may exist at a time, any existing socket is
 * closed.
 *
 * @param $rootScope - Scope used to $apply() app state changes
 *                     resulting from WebSocket messages, in order to update
 *                     appropriate watchers.
 * @param annotationMapper - The local annotation store
 * @param groups - The local groups store
 * @param session - Provides access to read and update the session state
 * @param settings - Application settings
 *
 * @return The push notification service client.
 */
// @ngInject
function connect($rootScope, annotationMapper, groups, session, settings) {
  // Get the socket URL
  var url = settings.websocketUrl;

  // Close any existing socket
  if (socket) {
    socket.close();
  }

  var configMessages = {};

  // Open the socket
  socket = new Socket(url);
  setConfig('client-id', {
    messageType: 'client_id',
    value: clientId
  });

  function handleAnnotationNotification(message) {
    action = message.options.action
    annotations = message.payload

    if (annotations.length === 0) {
      return;
    }

    // Discard annotations that aren't from the currently focused group.
    // FIXME: Have the server only send us annotations from the focused
    // group in the first place.
    annotations = annotations.filter(function (ann) {
      return ann.group == groups.focused().id
    });

    switch (action) {
      case 'create':
      case 'update':
      case 'past':
        annotationMapper.loadAnnotations(annotations);
        break;
      case 'delete':
        annotationMapper.unloadAnnotations(annotations);
        break;
    }
  }

  function handleSessionChangeNotification(message) {
    session.update(message.model);
  }

  function sendClientConfig () {
    Object.keys(configMessages).forEach(function (key) {
      if (configMessages[key]) {
        socket.send(configMessages[key]);
      }
    });
  }

  socket.on('open', function () {
    sendClientConfig();
  });

  socket.on('error', function (error) {
    console.warn('Error connecting to H push notification service:', error);
  });

  socket.on('message', function (event) {
    // wrap message dispatches in $rootScope.$apply() so that
    // scope watches on app state affected by the received message
    // are updated
    $rootScope.$apply(function () {
      message = JSON.parse(event.data);
      if (!message) {
        return;
      }

      if (message.type === 'annotation-notification') {
        handleAnnotationNotification(message)
      } else if (message.type === 'session-change') {
        handleSessionChangeNotification(message)
      } else {
        console.warn('received unsupported notification', message.type)
      }
    });
  });

  /**
   * Send a configuration message to the push notification service.
   * Each message is associated with a key, which is used to re-send
   * configuration data to the server in the event of a reconnection.
   */
  function setConfig(key, configMessage) {
    configMessages[key] = configMessage;
    if (socket.isConnected()) {
      socket.send(configMessage);
    }
  }

  return {
    setConfig: setConfig,
  };
}

module.exports = {
  connect: connect,
  clientId: clientId
};
