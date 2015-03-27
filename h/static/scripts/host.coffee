###*
# @ngdoc service
# @name host
#
# @description
# The `host` service relays the instructions the sidebar needs to send
# to the host document. (As opposed to all guests)
# It uses the bridge service to talk to the host.
###
module.exports = [
  '$window', 'bridge'
  ($window,   bridge) ->
    host =
      showSidebar: -> notifyHost method: 'showFrame'
      hideSidebar: -> notifyHost method: 'hideFrame'

    # Sends a message to the host frame
    notifyHost = (message) ->
      for {channel, window} in bridge.links when window is $window.parent
        channel.notify(message)
        break

    channelListeners =
      back: -> host.hideSidebar()
      open: -> host.showSidebar()

    for own channel, listener of channelListeners
      bridge.on(channel, listener)

    return host
]
