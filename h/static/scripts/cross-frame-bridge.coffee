class CrossFrameBridge

  # Connected links to other frames
  links: null

  options:
    # Scope identifier to distinguish this channel from any others
    scope: 'annotator:bridge'

    # Callbacks to invoke when a connection is established. The functions are
    # passed:
    # - the newly created channel object
    onConnectListeners: []

    # Any callbacks for messages on the channel. Max one callback per method.
    channelListeners: {}

  constructor: (options) ->
    @options = $.extend(true, {}, @options, options)
    @onConnectListeners = @options.onConnectListeners
    @channelListeners = @options.channelListeners
    @links = []

    # Start discovery of cooperating frames
    discoveryOptions =
      server: @options.server
      origin: @options.origin
    @crossFrameDiscovery = new CrossFrameDiscovery(discoveryOptions)
    onDiscoveryCallback = (source, origin, token) =>
      this._create_channel(source, origin, token)
    @crossFrameDiscovery.startDiscovery(onDiscoveryCallback)

  _create_channel: (source, origin, token) ->
    # Set up a channel
    scope = @options.scope + token
    channelOptions =
      window: source
      origin: origin
      scope: scope
      onReady: (channel) =>
        for callback in @onConnectListeners
          callback.call(this, channel, source)

    # Create the channel
    channel = this._build_channel channelOptions

    # Attach channel message listeners
    for method, callback of @channelListeners
        channel.bind method, callback

    # Store the newly created channel in our collection
    @links.push
      channel: channel
      window: source

    channel

  # Construct a channel to another frame
  _build_channel: (options) ->
    # jschannel chokes on FF and Chrome extension origins.
    if (options.origin.match /^chrome-extension:\/\//) or
        (options.origin.match /^resource:\/\//)
      options = $.extend {}, options, {origin: '*'}
    channel = Channel.build(options)

  # Make a method call on all links, collect the results and pass them to a
  # callback when all results are collected. Parameters:
  # - options.method (required): name of remote method to call
  # - options.params: parameters to pass to remote method
  # - options.callback: called with array of results
  call: (options) ->
    _makeDestroyFn = (c) =>
      (error, reason) =>
        c.destroy()
        @links = (l for l in @links when l.channel isnt c)

    deferreds = @links.map (l) ->
      d = $.Deferred().fail(_makeDestroyFn l.channel)
      callOptions = {
        method: options.method
        params: options.params
        success: (result) -> d.resolve result
        error: (error, reason) ->
          if error isnt 'timeout_error'
            d.reject error, reason
          else
            d.resolve null
        timeout: 1000
      }
      l.channel.call callOptions
      d.promise()

    $.when(deferreds...)
    .then (results...) =>
      options.callback? null, results
    .fail (failure) =>
      options.callback? failure

  # Publish a notification to all links
  notify: (options) ->
    for l in @links
      l.channel.notify options
    return

  on: (method, callback) ->
    @channelListeners[event] = callback
    for l in @links
      l.channel.bind event, callback
    return this

  off: (method) ->
    for l in @links
      l.channel.unbind event
    delete @channelListeners[event]
    return this

  # Add a function to be called upon a new connection
  onConnect: (callback) ->
    @onConnectListeners.push(callback)
