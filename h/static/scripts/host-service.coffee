###*
# @ngdoc service
# @name host
#
# @description
# The `host` service relay the instructions the sidebar needs to send
# to the host doument. (As opposed to all guests)
# It uses the cross-frame service to talk to the host.
###
class HostService

  this.inject = [ '$window', 'bridge' ]
  constructor:  (  $window,   bridge  ) ->

    # Sends a message to the host frame
    @_notifyHost = (message) ->
      for {channel, window} in bridge.links when window is $window.parent
        channel.notify(message)
        break

    channelListeners =
      back: @hideSidebar
      open: @showSidebar

    for own channel, listener of channelListeners
      bridge.on(channel, listener)

  # Tell the host to show the sidebar
  showSidebar: => @_notifyHost method: 'showFrame'

  # Tell the host to hide the sidebar
  hideSidebar: => @_notifyHost method: 'hideFrame'

angular.module('h').service('host', HostService)
