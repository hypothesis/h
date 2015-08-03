{module, inject} = angular.mock

describe 'AnnotationSync', ->
  sandbox = sinon.sandbox.create()
  publish = null
  fakeBridge = null
  createAnnotationSync = null
  createChannel = -> {call: sandbox.stub()}
  options = null
  PARENT_WINDOW = 'PARENT_WINDOW'

  before ->
    angular.module('h', [])
    .value('AnnotationSync', require('../annotation-sync'))

  beforeEach module('h')
  beforeEach inject (AnnotationSync, $rootScope) ->
    listeners = {}
    publish = (method, args...) -> listeners[method](args...)

    fakeWindow = parent: PARENT_WINDOW
    fakeBridge =
      on: sandbox.spy((method, fn) -> listeners[method] = fn)
      call: sandbox.stub()
      onConnect: sandbox.stub()
      links: []

    # TODO: Fix this hack to remove pre-existing bound listeners.
    $rootScope.$$listeners = []
    options =
      on: sandbox.spy (event, fn) ->
        $rootScope.$on(event, (evt, args...) -> fn(args...))
      emit: sandbox.spy($rootScope.$emit.bind($rootScope))

    createAnnotationSync = ->
      new AnnotationSync(fakeBridge, options)

  afterEach: -> sandbox.restore()

  describe 'the bridge connection', ->
    it 'sends over the current annotation cache', ->
      ann = {id: 1, $$tag: 'tag1'}
      annSync = createAnnotationSync()
      annSync.cache['tag1'] = ann

      channel = createChannel()
      fakeBridge.onConnect.yield(channel)

      assert.called(channel.call)
      assert.calledWith(channel.call, 'loadAnnotations',
        [tag: 'tag1', msg: ann])

    it 'does nothing if the cache is empty', ->
      annSync = createAnnotationSync()

      channel = createChannel()
      fakeBridge.onConnect.yield(channel)

      assert.notCalled(channel.call)

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
        publish(channelEvent, {msg: ann}, ->)
        assert.called(options.emit)
        assert.calledWith(options.emit, publishEvent, ann)

    assertReturnValue = (channelEvent) ->
      it 'calls back with a formatted annotation', (done) ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        callback = (err, ret) ->
          assert.isNull(err)
          assert.deepEqual(ret, {tag: 'tag1', msg: ann})
          done()
        publish(channelEvent, {msg: ann}, callback)

    assertCacheState = (channelEvent) ->
      it 'removes an existing entry from the cache before the event is triggered', ->
        options.emit = -> assert(!annSync.cache['tag1'])

        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache['tag1'] = ann

        publish(channelEvent, {msg: ann}, ->)

      it 'ensures the annotation is inserted in the cache', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        publish(channelEvent, {msg: ann}, ->)

        assert.equal(annSync.cache['tag1'], ann)

    describe 'the "beforeCreateAnnotation" event', ->
      assertBroadcast('beforeCreateAnnotation', 'beforeAnnotationCreated')
      assertReturnValue('beforeCreateAnnotation')
      assertCacheState('beforeCreateAnnotation')

    describe 'the "createAnnotation" event', ->
      assertBroadcast('createAnnotation', 'annotationCreated')
      assertReturnValue('createAnnotation')
      assertCacheState('createAnnotation')

    describe 'the "updateAnnotation" event', ->
      assertBroadcast('updateAnnotation', 'annotationUpdated')
      assertBroadcast('updateAnnotation', 'beforeAnnotationUpdated')
      assertReturnValue('updateAnnotation')
      assertCacheState('updateAnnotation')

    describe 'the "deleteAnnotation" event', ->
      assertBroadcast('deleteAnnotation', 'annotationDeleted')
      assertReturnValue('deleteAnnotation')

      it 'removes an existing entry from the cache before the event is triggered', ->
        options.emit = -> assert(!annSync.cache['tag1'])

        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache['tag1'] = ann

        publish('deleteAnnotation', {msg: ann}, ->)

      it 'removes the annotation from the cache', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        publish('deleteAnnotation', {msg: ann}, ->)

        assert(!annSync.cache['tag1'])

    describe 'the "sync" event', ->
      it 'calls back with parsed and formatted annotations', (done) ->
        options.parser = sinon.spy((x) -> x)
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()

        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3, $$tag: 'tag3'}]
        bodies = ({msg: ann, tag: ann.$$tag} for ann in annotations)

        callback = (err, ret) ->
          assert.isNull(err)
          assert.deepEqual(ret, bodies)
          assert.called(options.parser)
          assert.called(options.formatter)
          done()

        publish('sync', bodies, callback)

    describe 'the "loadAnnotations" event', ->
      it 'publishes the "loadAnnotations" event with parsed annotations', ->
        options.parser = sinon.spy((x) -> x)
        annSync = createAnnotationSync()

        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3, $$tag: 'tag3'}]
        bodies = ({msg: ann, tag: ann.$$tag} for ann in annotations)
        publish('loadAnnotations', bodies, ->)

        assert.called(options.parser)
        assert.calledWith(options.emit, 'loadAnnotations', annotations)

  describe 'application event handlers', ->
    describe 'the "beforeAnnotationCreated" event', ->
      it 'proxies the event over the bridge', ->
        ann = {id: 1}
        annSync = createAnnotationSync()
        options.emit('beforeAnnotationCreated', ann)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'beforeCreateAnnotation',
          {msg: ann, tag: ann.$$tag}, sinon.match.func)

      it 'returns early if the annotation has a tag', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        options.emit('beforeAnnotationCreated', ann)

        assert.notCalled(fakeBridge.call)

    describe 'the "annotationCreated" event', ->
      it 'proxies the event over the bridge', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationCreated', ann)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'createAnnotation',
          {msg: ann, tag: ann.$$tag}, sinon.match.func)

      it 'returns early if the annotation has a tag but is not cached', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        options.emit('annotationCreated', ann)

        assert.notCalled(fakeBridge.call)

      it 'returns early if the annotation has no tag', ->
        ann = {id: 1}
        annSync = createAnnotationSync()
        options.emit('annotationCreated', ann)

        assert.notCalled(fakeBridge.call)

    describe 'the "annotationUpdated" event', ->
      it 'proxies the event over the bridge', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationUpdated', ann)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'updateAnnotation',
          {msg: ann, tag: ann.$$tag}, sinon.match.func)

      it 'returns early if the annotation has a tag but is not cached', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        options.emit('annotationUpdated', ann)

        assert.notCalled(fakeBridge.call)

      it 'returns early if the annotation has no tag', ->
        ann = {id: 1}
        annSync = createAnnotationSync()
        options.emit('annotationUpdated', ann)

        assert.notCalled(fakeBridge.call)

    describe 'the "annotationDeleted" event', ->
      it 'proxies the event over the bridge', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'deleteAnnotation',
          {msg: ann, tag: ann.$$tag}, sinon.match.func)

      it 'parses the result returned by the call', ->
        ann = {id: 1, $$tag: 'tag1'}
        options.parser = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        body = {msg: {}, tag: 'tag1'}
        fakeBridge.call.yield(null, [body])
        assert.called(options.parser)
        assert.calledWith(options.parser, {})

      it 'removes the annotation from the cache on success', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        fakeBridge.call.yield(null, [])
        assert.isUndefined(annSync.cache.tag1)

      it 'does not remove the annotation from the cache if an error occurs', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        fakeBridge.call.yield(new Error('Error'), [])
        assert.equal(annSync.cache.tag1, ann)

      it 'returns early if the annotation has a tag but is not cached', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        options.emit('annotationDeleted', ann)

        assert.notCalled(fakeBridge.call)

      it 'returns early if the annotation has no tag', ->
        ann = {id: 1}
        annSync = createAnnotationSync()
        options.emit('annotationDeleted', ann)

        assert.notCalled(fakeBridge.call)

    describe 'the "annotationsLoaded" event', ->
      it 'formats the provided annotations', ->
        annotations = [{id: 1}, {id: 2}, {id: 3}]
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', annotations)

        assert.calledWith(options.formatter, {id: 1})
        assert.calledWith(options.formatter, {id: 2})
        assert.calledWith(options.formatter, {id: 3})

      it 'sends the annotations over the bridge', ->
        annotations = [{id: 1}, {id: 2}, {id: 3}]
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', annotations)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'loadAnnotations',
          ({msg: a, tag: a.$$tag} for a in annotations))

      it 'does not send annotations that have already been tagged', ->
        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3}]
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', annotations)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, 'loadAnnotations',
          [{msg: annotations[2], tag: annotations[2].$$tag}])

      it 'returns early if no annotations are loaded', ->
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', [])

        assert.notCalled(fakeBridge.call)
