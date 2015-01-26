assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'AnnotationUISync', ->
  sandbox = sinon.sandbox.create()
  uiSync = null
  fakeBridge = null
  createAnnotationUISync = null
  PARENT_WINDOW = {}

  beforeEach module('h')
  beforeEach inject (AnnotationUISync) ->
    fakeWindow = parent: PARENT_WINDOW
    fakeBridge =
      on: sandbox.stub()
      notify: sandbox.stub()
      onConnect: sandbox.stub()
    fakeAnnotationSync =
      getAnnotationForTag: (x) -> x
    fakeAnnotationUI =
      focusAnnotations: sandbox.stub()
      selectAnnotations: sandbox.stub()
      xorSelectedAnnotations: sandbox.stub()
      tool: 'comment'
      visibleHighlights: false

    createAnnotationUISync = ->
      new AnnotationUISync(
        fakeWindow, fakeBridge, fakeAnnotationSync, fakeAnnotationUI)

  afterEach: -> sandbox.restore()

  describe 'on bridge connection', ->
    describe 'when the source is not the parent window', ->
      it 'broadcasts the tool/visibility settings to the channel', ->
        channel = notify: sandbox.stub()
        fakeBridge.onConnect.callsArgWith(0, channel, {})

        createAnnotationUISync()

        assert.calledWith(channel.notify, {
          method: 'setTool'
          params: 'comment'
        })

        assert.calledWith(channel.notify, {
          method: 'setVisibleHighlights'
          params: false
        })

    describe 'when the source is the parent window', ->
      it 'does nothing', ->
        channel = notify: sandbox.stub()
        fakeBridge.onConnect.callsArgWith(0, channel, PARENT_WINDOW)

        createAnnotationUISync()
        assert.notCalled(channel.notify)

  describe 'on "back" event', ->
    it 'sends the "hideFrame" message to the host only'

  describe 'on "open" event', ->
    it 'sends the "showFrame" message to the host only'

  describe 'on "showEditor" event', ->
    it 'sends the "showFrame" message to the host only'

  describe 'on "showAnnotations" event', ->
    it 'sends the "showFrame" message to the host only'
    it 'updates the annotationUI to include the shown annotations'

  describe 'on "focusAnnotations" event', ->
    it 'updates the annotationUI to show the provided annotations'

  describe 'on "toggleAnnotationSelection" event', ->
    it 'updates the annotationUI to show the provided annotations'

  describe 'on "setTool" event', ->
    it 'updates the annotationUI with the new tool'
    it 'notifies the other frames of the change'

  describe 'on "setVisibleHighlights" event', ->
    it 'updates the annotationUI with the new value'
    it 'notifies the other frames of the change'
