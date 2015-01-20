# Instantiates all objects used for cross frame discovery and communication.
setupCrossFrameCommunication = [
  '$document', 'setupCrossFrameSync', 'setupToolkitSync', 'Bridge', 'Discovery'
  ($document,   setupCrossFrameSync,   setupToolkitSync,   Bridge,   Discovery) ->
    bridge = new Bridge()
    discovery = new Discovery($document)

    setupToolkitSync(bridge)
    setupCrossFrameSync(bridge)

    discovery.find (source, origin, scope) ->
      bridge.add(source, origin, scope)
]

angular.module('h')
.value('setupCrossFrameCommunication', setupCrossFrameCommunication)
