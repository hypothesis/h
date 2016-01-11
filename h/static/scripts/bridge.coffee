Promise = require('core-js/library/es6/promise')
extend = require('extend')
RPC = require('./frame-rpc')

# The Bridge service sets up a channel between frames
# and provides an events API on top of it.
module.exports = class Bridge
  # Connected links to other frames
  links: null
  channelListeners: null
  onConnectListeners: null

  constructor: ->
    @links = []
    @channelListeners = {}
    @onConnectListeners = []

  createChannel: (source, origin, token) ->
    channel = null
    connected = false

    ready = =>
      return if connected
      connected = true
      for cb in @onConnectListeners
        cb.call(null, channel, source)

    connect = (_token, cb) =>
      if _token is token
        cb()
        ready()

    listeners = extend({connect}, @channelListeners)

    # Set up a channel
    channel = new RPC(window, source, origin, listeners)

    # Fire off a connection attempt
    channel.call('connect', token, ready)

    # Store the newly created channel in our collection
    @links.push
      channel: channel
      window: source

    channel

  # Make a method call on all links, collect the results and pass them to a
  # callback when all results are collected. Parameters:
  # - method (required): name of remote method to call
  # - args...: parameters to pass to remote method
  # - callback: (optional) called with error, if any, and an Array of results
  call: (method, args...) ->
    cb = null
    if typeof(args[args.length - 1]) is 'function'
      cb = args[args.length - 1]
      args = args.slice(0, -1)

    _makeDestroyFn = (c) =>
      (error) =>
        c.destroy()
        @links = (l for l in @links when l.channel isnt c)
        throw error

    promises = @links.map (l) ->
      p = new Promise (resolve, reject) ->
        timeout = setTimeout((-> resolve(null)), 1000)
        try
          l.channel.call method, args..., (err, result) ->
            clearTimeout(timeout)
            if err then reject(err) else resolve(result)
        catch err
          reject(err)

      # Don't assign here. The disconnect is handled asynchronously.
      return p.catch(_makeDestroyFn(l.channel))

    resultPromise = Promise.all(promises)

    if cb?
      resultPromise = resultPromise
        .then((results) -> cb(null, results))
        .catch((error) -> cb(error))

    return resultPromise

  on: (method, callback) ->
    if @channelListeners[method]
      throw new Error("Listener '#{method}' already bound in Bridge")
    @channelListeners[method] = callback
    return this

  off: (method) ->
    delete @channelListeners[method]
    return this

  # Add a function to be called upon a new connection
  onConnect: (callback) ->
    @onConnectListeners.push(callback)
    this
