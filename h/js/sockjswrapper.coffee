class SockJSWrapper
  transports: ['xhr-streaming', 'iframe-eventsource', 'iframe-htmlfile', 'xhr-polling', 'iframe-xhr-polling', 'jsonp-polling']
  path: window.location.protocol + '//' + window.location.hostname + ':' + window.location.port + '/__streamer__'

  constructor: ($scope, filter, fn_open, fn_message, fn_close) ->
    sock = new SockJS(path, transports)

    sock.onopen = ->
      sock.send JSON.stringify filter
      if fn_open? then fn_open()

    sock.onclose = fn_close

    sock.onmessage = (msg) =>
      console.log 'Got something'
      console.log msg
      data = msg.data[0]
      action = msg.data[1]
      unless data instanceof Array then data = [data]
      if fn_message?
        $scope.$apply =>
          fn_message data, action

