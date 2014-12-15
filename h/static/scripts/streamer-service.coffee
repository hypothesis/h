ST_CLOSED = 1
ST_CONNECTING = 2
ST_OPEN = 3

###*
# @ngdoc service
# @name Streamer
#
# @param {String} url The base URL for the socket connection
#
# @description
# Provides access to the streamer websocket.
###
class Streamer
  constructor: (transport, url) ->
    this.onmessage = ->

    this._failCount = 0
    this._queue = []
    this._state = ST_CLOSED
    this._transport = transport
    this._url = url

  ###*
  # @ngdoc method
  # @name Streamer#open
  #
  # @description
  # Open the streamer websocket if it is not already open or connecting. Handles
  # connection failures and sets up onmessage handlers.
  ###
  open: ->
    if this._state == ST_OPEN || this._state == ST_CONNECTING
      return

    self = this
    this._sock = new this._transport(this._url)
    this._state = ST_CONNECTING

    this._sock.onopen = ->
      self._state = ST_OPEN
      self._failCount = 0

      clientId = uuid.v4()
      setAjaxClientId(clientId)

      # Generate and send our client ID
      self.send({
        messageType: 'client_id'
        value: clientId
      })
      # Process queued messages
      self._sendQueue()

    this._sock.onclose = ->
      self._state = ST_CLOSED
      self._failCount++

      setTimeout((-> self.open()), backoff(self._failCount, 10))

    this._sock.onmessage = (msg) ->
      self.onmessage(JSON.parse(msg))

  ###*
  # @ngdoc method
  # @name Streamer#close
  #
  # @description
  # Close the streamer socket.
  ###
  close: ->
    if this._state == ST_CLOSED
      return

    this._sock.onclose = ->
    this._sock.close()
    this._sock = null
    this._state = ST_CLOSED

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

setAjaxClientId = (clientId) ->
  $.ajaxSetup({
    headers: {
      'X-Client-Id': clientId
    }
  })

streamerProvider = ->
  provider = {}
  provider.url = null
  provider.$get = ['$window', ($window) ->
    new Streamer($window.WebSocket, provider.url)
  ]
  return provider


angular.module('h.streamer', [])
.provider('streamer', streamerProvider)
