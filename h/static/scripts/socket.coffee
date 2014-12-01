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


socket = ['documentHelpers', 'clientID', (documentHelpers, clientID) ->
  ->
    uri = "#{documentHelpers.baseURI}ws".replace /^http/, 'ws'
    sock = new WebSocket(uri)
    send = sock.send
    sock.send = (data) ->
      # Set the client ID before the first message.
      cid = JSON.stringify
        messageType: 'client_id'
        value: clientID

      # Send the messages.
      send.call(sock, cid)
      send.call(sock, data)

      # Restore the original send method.
      sock.send = send

    sock
]


angular.module('h')
.factory('clientID', clientID)
.factory('socket', socket)
.run(run)
