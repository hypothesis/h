{module, inject} = angular.mock

describe 'AnnotationUISync', ->
  sandbox = sinon.sandbox.create()
  $digest = null
  uiSync = null
  publish = null
  fakeBridge = null
  fakeAnnotationUI = null
  fakeAnnotationSync = null
  createAnnotationUISync = null
  createChannel = -> {call: sandbox.stub()}
  PARENT_WINDOW = 'PARENT_WINDOW'

  before ->
    angular.module('h', [])
    .value('AnnotationUISync', require('../annotation-ui-sync'))

  beforeEach module('h')
  beforeEach inject (AnnotationUISync, $rootScope) ->
    $digest = sandbox.stub($rootScope, '$digest')
    listeners = {}
    publish = (method, args...) -> listeners[method](args...)

    fakeWindow = parent: PARENT_WINDOW
    fakeBridge =
      on: sandbox.spy((method, fn) -> listeners[method] = fn)
      call: sandbox.stub()
      onConnect: sandbox.stub()
      links: [
        {window: PARENT_WINDOW,    channel: createChannel()}
        {window: 'ANOTHER_WINDOW', channel: createChannel()}
        {window: 'THIRD_WINDOW',   channel: createChannel()}
      ]
    fakeAnnotationSync =
      getAnnotationForTag: (tag) -> {id: Number(tag.replace('tag', ''))}
    fakeAnnotationUI =
      focusAnnotations: sandbox.stub()
      selectAnnotations: sandbox.stub()
      xorSelectedAnnotations: sandbox.stub()
      visibleHighlights: false

    createAnnotationUISync = ->
      new AnnotationUISync(
        $rootScope, fakeWindow, fakeBridge, fakeAnnotationSync, fakeAnnotationUI)

  afterEach: -> sandbox.restore()

  describe 'on bridge connection', ->
    describe 'when the source is not the parent window', ->
      it 'broadcasts the visibility settings to the channel', ->
        channel = createChannel()
        fakeBridge.onConnect.callsArgWith(0, channel, {})

        createAnnotationUISync()

        assert.calledWith(channel.call, 'setVisibleHighlights', false)

    describe 'when the source is the parent window', ->
      it 'does nothing', ->
        channel = call: sandbox.stub()
        fakeBridge.onConnect.callsArgWith(0, channel, PARENT_WINDOW)

        createAnnotationUISync()
        assert.notCalled(channel.call)

  describe 'on "showAnnotations" event', ->
    it 'updates the annotationUI to include the shown annotations', ->
      createAnnotationUISync()
      publish('showAnnotations', ['tag1', 'tag2', 'tag3'])
      assert.called(fakeAnnotationUI.selectAnnotations)
      assert.calledWith(fakeAnnotationUI.selectAnnotations, [
        {id: 1}, {id: 2}, {id: 3}
      ])

    it 'triggers a digest', ->
      createAnnotationUISync()
      publish('showAnnotations', ['tag1', 'tag2', 'tag3'])
      assert.called($digest)

  describe 'on "focusAnnotations" event', ->
    it 'updates the annotationUI to show the provided annotations', ->
      createAnnotationUISync()
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3'])
      assert.called(fakeAnnotationUI.focusAnnotations)
      assert.calledWith(fakeAnnotationUI.focusAnnotations, [
        {id: 1}, {id: 2}, {id: 3}
      ])

    it 'triggers a digest', ->
      createAnnotationUISync()
      publish('focusAnnotations', ['tag1', 'tag2', 'tag3'])
      assert.called($digest)

  describe 'on "toggleAnnotationSelection" event', ->
    it 'updates the annotationUI to show the provided annotations', ->
      createAnnotationUISync()
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3'])
      assert.called(fakeAnnotationUI.xorSelectedAnnotations)
      assert.calledWith(fakeAnnotationUI.xorSelectedAnnotations, [
        {id: 1}, {id: 2}, {id: 3}
      ])

    it 'triggers a digest', ->
      createAnnotationUISync()
      publish('toggleAnnotationSelection', ['tag1', 'tag2', 'tag3'])
      assert.called($digest)

  describe 'on "setVisibleHighlights" event', ->
    it 'updates the annotationUI with the new value', ->
      createAnnotationUISync()
      publish('setVisibleHighlights', true)
      assert.equal(fakeAnnotationUI.visibleHighlights, true)

    it 'notifies the other frames of the change', ->
      createAnnotationUISync()
      publish('setVisibleHighlights', true)
      assert.calledWith(fakeBridge.call, 'setVisibleHighlights', true)

    it 'triggers a digest of the application state', ->
      createAnnotationUISync()
      publish('setVisibleHighlights', true)
      assert.called($digest)
