# A module for establishing connections between multiple frames in the same
# document. This model requires one frame (and only one) to be designated the
# server (created with options.server: true) which can then connect to as
# many clients as required. Once a handshake between two frames has been
# completed the onDiscovery callback will be called with information about
# both frames.
#
# Example:
#
#   // host.html
#   var server = new Discovery(window, {server: true})
#   server.startDiscovery(function (window, source, token) {
#     // Establish a message bus to the new client window.
#     server.stopDiscovery();
#   }
#
#   // client.html
#   var client = new Discovery(window)
#   client.startDiscovery(function (window, source, token) {
#     // Establish a message bus to the new server window.
#     server.stopDiscovery();
#   }
module.exports = class Discovery
  # Origins allowed to communicate on the channel
  server: false

  # When this is true, this bridge will act as a server and, similar to DHCP,
  # offer to connect to bridges in other frames it discovers.
  origin: '*'

  onDiscovery: null
  requestInProgress: false

  # Accepts a target window and an object of options. The window provided will
  # act as a starting point for discovering other windows.
  constructor: (@target, options={}) ->
    @server = options.server if options.server
    @origin = options.origin if options.origin

  startDiscovery: (onDiscovery) ->
    if @onDiscovery
      throw new Error('Discovery is already in progress, call .stopDiscovery() first')

    # Find other frames that run the same discovery mechanism. Sends a beacon
    # and listens for beacons.
    #
    # Parameters:
    # onDiscovery: (source, origin, token) -> ()
    #   When two frames discover each other, onDiscovery will be called on both
    #   sides with the same token string.
    @onDiscovery = onDiscovery

    # Listen to discovery messages from other frames
    @target.addEventListener('message', this._onMessage, false)

    # Send a discovery message to other frames to create channels
    this._beacon()
    return

  stopDiscovery: =>
    # Remove the listener for discovery messages
    @onDiscovery = null
    @target.removeEventListener('message', this._onMessage)
    return


  # Send out a beacon to discover frames to connect with
  _beacon: ->
    beaconMessage = if @server
      '__cross_frame_dhcp_offer'
    else
      '__cross_frame_dhcp_discovery'

    # Starting at the top window, walk through all frames, and ping each frame
    # that is not our own.
    queue = [@target.top]
    while queue.length
      parent = queue.shift()
      if parent isnt @target
        parent.postMessage(beaconMessage, @origin)
      for child in parent.frames
        queue.push(child)
    return


  _onMessage: (event) =>
    {source, origin, data} = event

    # If `origin` is 'null' the source frame is a file URL or loaded over some
    # other scheme for which the `origin` is undefined. In this case, the only
    # way to ensure the message arrives is to use the wildcard origin. See:
    #
    #   https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage
    #
    # When sending messages to or from a Firefox WebExtension, current
    # versions of Firefox have a bug that causes the origin check to fail even
    # though the target and actual origins of the message match.
    if origin is 'null' || origin.match('moz-extension:') ||
       window.location.protocol == 'moz-extension:'
      origin = '*'

    # Check if the message is at all related to our discovery mechanism
    match = data.match? /^__cross_frame_dhcp_(discovery|offer|request|ack)(?::(\d+))?$/
    return unless match

    # Read message type and optional token from message data
    messageType = match[1]
    token = match[2]

    # Process the received message
    {reply, discovered, token} = this._processMessage(messageType, token, origin)

    if reply
      source.postMessage '__cross_frame_dhcp_' + reply, origin

    if discovered
      @onDiscovery.call(null, source, origin, token)

    return

  _processMessage: (messageType, token, origin) ->
    # Process an incoming message, returns:
    # - a reply message
    # - whether the discovery has completed
    reply = null
    discovered = false

    if @server # We are configured as server
      if messageType is 'discovery'
        # A client joined the party. Offer it to connect.
        reply = 'offer'
      else if messageType is 'request'
        # Create a channel with random identifier
        token = this._generateToken()
        reply = 'ack' + ':' + token
        discovered = true
      else if messageType is 'offer' or messageType is 'ack'
        throw new Error("""
          A second Discovery server has been detected at #{origin}.
          This is unsupported and will cause unexpected behaviour.""")
    else # We are configured as a client
      if messageType is 'offer'
        # The server joined the party, or replied to our discovery message.
        # Request it to set up a channel if we did not already do so.
        unless @requestInProgress
          @requestInProgress = true # prevent creating two channels
          reply = 'request'
      else if messageType is 'ack'
        # The other side opened a channel to us. We note its scope and create
        # a matching channel end on this side.
        @requestInProgress = false # value should not actually matter anymore.
        discovered = true
    return {reply: reply, discovered: discovered, token: token}

  _generateToken: ->
    ('' + Math.random()).replace(/\D/g, '')
