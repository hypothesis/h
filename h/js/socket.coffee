imports = [
  'h.helpers'
]


clientID = ->
  # Generate client ID
  buffer = (new Array(16))
  uuid.v4 null, buffer, 0
  uuid.unparse buffer


run = ['clientID', (clientID) ->
  $.ajaxSetup
    headers:
      "X-Client-Id": clientID
]

socket = ['baseURI', 'clientID', (baseURI, clientID) ->
  -> new Socket(clientID, "#{baseURI}__streamer__")
]


class Socket extends SockJS
  constructor: (clientID, args...)->
    SockJS.apply(this, args)

    send = this.send
    this.send = (data) =>
      # Set the client ID before the first message.
      cid = JSON.stringify
        messageType: 'client_id'
        value: clientID

      # Send the messages.
      send.call(this, cid)
      send.call(this, data)

      # Restore the original send method.
      this.send = send


angular.module('h.socket', imports, configure)
.factory('clientID', clientID)
.factory('socket', socket)
.run(run)
