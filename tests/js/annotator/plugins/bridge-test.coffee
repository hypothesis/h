assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Plugin.Bridge', ->
  sandbox = sinon.sandbox.create()
  createGuest = (options) ->
    element = document.createElement('div')
    return new Annotator.Plugin.Bridge(element, options || {})

  afterEach -> sandbox.restore()

  describe 'constructor', ->
    it 'instantiates the CrossFrameDiscovery component'
    it 'instantiates the CrossFrameBridge component'
    it 'instantiates the AnnotationSync component'

  describe '.pluginInit', ->
    it 'starts the discovery of new channels'
    it 'creates a channel when a new frame is discovered'

  describe '.destroy', ->
    it 'stops the discovery of new frames'

  describe '.sync', ->
    it 'syncs the annotations with the other frame'
