assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'AnnotationSync', ->
  sandbox = sinon.sandbox.create()
  publish = null
  fakeBridge = null
  createAnnotationSync = null
  createChannel = -> {notify: sandbox.stub()}
  options = null
  PARENT_WINDOW = 'PARENT_WINDOW'

  beforeEach module('h')
  beforeEach inject (AnnotationSync) ->
    listeners = {}
    publish = ({method, params}) -> listeners[method]('ctx', params)

    fakeWindow = parent: PARENT_WINDOW
    fakeBridge =
      on: sandbox.spy((method, fn) -> listeners[method] = fn)
      notify: sandbox.stub()
      onConnect: sandbox.stub()
      links: [
        {window: PARENT_WINDOW,    channel: createChannel()}
        {window: 'ANOTHER_WINDOW', channel: createChannel()}
        {window: 'THIRD_WINDOW',   channel: createChannel()}
      ]
    options =
      on: sandbox.stub()
      emit: sandbox.stub()

    createAnnotationSync = ->
      new AnnotationSync(options, fakeBridge)

  afterEach: -> sandbox.restore()

  describe 'on bridge connection', ->
    it 'sends over the current annotation cache', ->
      ann = {id: 1, $$tag: 'tag1'}
      annSync = createAnnotationSync()
      annSync.cache['tag1'] = ann

      channel = createChannel()
      fakeBridge.onConnect.yield(channel)

      assert.called(channel.notify)
      assert.calledWith(channel.notify, {
        method: 'loadAnnotations'
        params: [tag: 'tag1', msg: ann]
      })

    it 'does nothing if the cache is empty', ->
      annSync = createAnnotationSync()

      channel = createChannel()
      fakeBridge.onConnect.yield(channel)

      assert.notCalled(channel.notify)

  describe '.getAnnotationForTag', ->
    it 'returns the annotation if present in the cache', ->
      ann = {id: 1, $$tag: 'tag1'}
      annSync = createAnnotationSync()
      annSync.cache['tag1'] = ann

      cached = annSync.getAnnotationForTag('tag1')
      assert.equal(cached, ann)

    it 'returns null if not present in the cache', ->
      annSync = createAnnotationSync()
      cached = annSync.getAnnotationForTag('tag1')
      assert.isNull(cached)

  describe 'channel event handlers', ->
    assertBroadcast = (channelEvent, publishEvent) ->
      it 'broadcasts the "' + publishEvent + '" event over the local event bus', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        publish(method: channelEvent, params: {msg: ann})
        assert.called(options.emit)
        assert.calledWith(options.emit, publishEvent, ann)

    assertReturnValue = (channelEvent) ->
      it 'returns a formatted annotation to be sent to the calling frame', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        ret = publish(method: channelEvent, params: {msg: ann})

        assert.deepEqual(ret, {tag: 'tag1', msg: ann})

    assertCacheState = (channelEvent) ->
      it 'removes an existing entry from the cache before the event is triggered', ->
        options.emit = -> assert(!annSync.cache['tag1'])

        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache['tag1'] = ann

        publish(method: channelEvent, params: {msg: ann})

      it 'ensures the annotation is inserted in the cache', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        publish(method: channelEvent, params: {msg: ann})

        assert.equal(annSync.cache['tag1'], ann)

    describe 'on "beforeCreateAnnotation" event', ->
      assertBroadcast('beforeCreateAnnotation', 'beforeAnnotationCreated')
      assertReturnValue('beforeCreateAnnotation')
      assertCacheState('beforeCreateAnnotation')

    describe 'on "createAnnotation" event', ->
      assertBroadcast('createAnnotation', 'annotationCreated')
      assertReturnValue('createAnnotation')
      assertCacheState('createAnnotation')

    describe 'on "updateAnnotation" event', ->
      assertBroadcast('updateAnnotation', 'annotationUpdated')
      assertBroadcast('updateAnnotation', 'beforeAnnotationUpdated')
      assertReturnValue('updateAnnotation')
      assertCacheState('updateAnnotation')

    describe 'on "deleteAnnotation" event', ->
      assertBroadcast('deleteAnnotation', 'annotationDeleted')
      assertReturnValue('deleteAnnotation')

      it 'removes an existing entry from the cache before the event is triggered', ->
        options.emit = -> assert(!annSync.cache['tag1'])

        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache['tag1'] = ann

        publish(method: 'deleteAnnotation', params: {msg: ann})

      it 'removes the annotation from the cache', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        publish(method: 'deleteAnnotation', params: {msg: ann})

        assert(!annSync.cache['tag1'])

