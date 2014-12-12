getClientId = ->
  # Generate client ID
  buffer = (new Array(16))
  uuid.v4 null, buffer, 0
  uuid.unparse buffer


socket = ['documentHelpers', (documentHelpers) ->
  -> new Socket("#{documentHelpers.baseURI}__streamer__")
]


class Socket extends SockJS
  constructor: ->
    SockJS.apply(this, arguments)

    send = this.send
    this.send = (data) =>
      clientId = getClientId()

      $.ajaxSetup
        headers:
          "X-Client-Id": clientId

      # Set the client ID before the first message.
      cid = JSON.stringify
        messageType: 'client_id'
        value: clientId

      # Send the messages.
      send.call(this, cid)
      send.call(this, data)

      # Restore the original send method.
      this.send = send


angular.module('h')
.factory('socket', socket)
