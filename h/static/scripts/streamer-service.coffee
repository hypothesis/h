ST_CONNECTING = 0
ST_OPEN = 1
ST_CLOSING = 2
ST_CLOSED = 3

###*
# @ngdoc service
# @name streamer
#
# @property {string} clientId A unique identifier for this client.
#
# @description
# Provides access to the streamer websocket.
###
class Streamer
  constructor: ->
    this.clientId = null

    this.onopen = angular.noop
    this.onclose = angular.noop
    this.onmessage = angular.noop

    this._failCount = 0
    this._queue = []
    this._state = ST_CLOSED

  ###*
  # @ngdoc method
  # @name Streamer#open
  #
  # @param {Object} transport The transport class to create.
  # @param {string} url The URL to which to connect.
  # @param {Object|Array} protocols The protocol (or protocols) to use.
  #
  # @description
  # Open the streamer websocket if it is not already open or connecting. Handles
  # connection failures and sets up onmessage handlers.
  ###
  open: (transport, url, protocols) ->
    if this._state == ST_OPEN || this._state == ST_CONNECTING
      return

    self = this

    if protocols
      this._sock = new transport(url, protocols)
    else
      this._sock = new transport(url)

    this._state = ST_CONNECTING

    this._sock.onopen = ->
      self._state = ST_OPEN
      self._failCount = 0

      # Send the client id
      if self.clientId
        self.send(messageType: 'client_id', value: self.clientId)

      # Give the application a chance to initialize the connection
      self.onopen(name: 'open')
      # Process queued messages
      self._sendQueue()

    this._sock.onclose = ->
      self._state = ST_CLOSED
      self._failCount++

      reconnect = angular.bind(self, self.open, transport, url, protocols)
      waitFor = backoff(self._failCount, 10)
      setTimeout(reconnect, waitFor)

    this._sock.onmessage = (msg) ->
      self.onmessage(JSON.parse(msg.data))

  ###*
  # @ngdoc method
  # @name Streamer#close
  #
  # @description
  # Close the streamer socket.
  ###
  close: ->
    if this._state == ST_CLOSING or this._state == ST_CLOSED
      return

    self = this

    this._sock.onclose = ->
      self._state = ST_CLOSED
      self.onclose()

    this._sock.close()
    this._sock = null
    this._state = ST_CLOSING

  ###*
  # @ngdoc method
  # @name Streamer#send
  #
  # @param {Object} data Message data
  #
  # @description
  # Send an object down the streamer websocket. This can be called before the
  # socket is open: the message will be queued and delivered once a connection
  # is established.
  ###
  send: (data) ->
    if this._state == ST_OPEN
      this._sock.send(JSON.stringify(data))
    else
      this._queue.push(data)

  _sendQueue: ->
    while msg = this._queue.shift()
      this.send(msg)


backoff = (index, max) ->
  index = Math.min(index, max)
  return 500 * Math.random() * (Math.pow(2, index) - 1)


angular.module('h.streamer', [])
.service('streamer', Streamer)
