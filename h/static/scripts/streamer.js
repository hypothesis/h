var uuid = require('node-uuid')

// the randomly generated session UUID
var clientId = uuid.v4();

// the singleton socket instance, only one may
// be open at a time
var socket;

var logger = require('./logger').getLogger('websocket');

/**
 * Open a new WebSocket connection to the Hypothesis push notification service.
 * Only one websocket connection may exist at a time, any existing socket is
 * closed.
 *
 * @param $websocket - angular-websocket constructor
 * @param annotationMapper - The local annotation store
 * @param groups - The local groups store
 * @param session - Provides access to read and update the session state
 * @param settings - Application settings
 *
 * @return An angular-websocket wrapper around the socket.
 */
// @ngInject
function connect($websocket, annotationMapper, groups, session, settings) {
  // Get the socket URL
  var url = settings.websocketUrl;

  // Close any existing socket
  if (socket) {
    socket.close();
  }

  // Open the socket
  socket = $websocket(url, [], {
    reconnectIfNotNormalClose: true
  });
  socket.send({
    messageType: 'client_id',
    value: clientId
  })

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

  // Listen for updates
  socket.onMessage(function (event) {
    message = JSON.parse(event.data);
    if (!message) {
      logger.warn('failed to parse message', event.data);
      return;
    }
    logger.debug('received message', message);

    if (message.type === 'annotation-notification') {
      handleAnnotationNotification(message)
    } else if (message.type === 'session-change') {
      handleSessionChangeNotification(message)
    } else {
      logger.warn('received unsupported notification', message.type)
    }
  });

  return socket
}

module.exports = {
  connect: connect,
  clientId: clientId
};
