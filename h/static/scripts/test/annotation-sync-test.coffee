{module, inject} = require('angular-mock')

describe 'AnnotationSync', ->
  sandbox = sinon.sandbox.create()
  publish = null
  fakeBridge = null
  createAnnotationSync = null
  createChannel = -> {notify: sandbox.stub()}
  options = null
  PARENT_WINDOW = 'PARENT_WINDOW'

  before ->
    angular.module('h', [])
    .value('AnnotationSync', require('../annotation-sync'))

  beforeEach module('h')
  beforeEach inject (AnnotationSync, $rootScope) ->
    listeners = {}
    publish = ({method, params}) -> listeners[method]('ctx', params)

    fakeWindow = parent: PARENT_WINDOW
    fakeBridge =
      on: sandbox.spy((method, fn) -> listeners[method] = fn)
      call: sandbox.stub()
      notify: sandbox.stub()
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

        publish(method: 'deleteAnnotation', params: {msg: ann})

      it 'removes the annotation from the cache', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()

        publish(method: 'deleteAnnotation', params: {msg: ann})

        assert(!annSync.cache['tag1'])

    describe 'the "sync" event', ->
      it 'returns an array of parsed and formatted annotations', ->
        options.parser = sinon.spy((x) -> x)
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()

        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3, $$tag: 'tag3'}]
        bodies = ({msg: ann, tag: ann.$$tag} for ann in annotations)
        ret = publish(method: 'sync', params: bodies)

        assert.deepEqual(ret, ret)
        assert.called(options.parser)
        assert.called(options.formatter)

    describe 'the "loadAnnotations" event', ->
      it 'publishes the "loadAnnotations" event with parsed annotations', ->
        options.parser = sinon.spy((x) -> x)
        annSync = createAnnotationSync()

        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3, $$tag: 'tag3'}]
        bodies = ({msg: ann, tag: ann.$$tag} for ann in annotations)
        ret = publish(method: 'loadAnnotations', params: bodies)

        assert.called(options.parser)
        assert.calledWith(options.emit, 'loadAnnotations', annotations)

  describe 'application event handlers', ->
    describe 'the "beforeAnnotationCreated" event', ->
      it 'proxies the event over the bridge', ->
        ann = {id: 1}
        annSync = createAnnotationSync()
        options.emit('beforeAnnotationCreated', ann)

        assert.called(fakeBridge.call)
        assert.calledWith(fakeBridge.call, {
          method: 'beforeCreateAnnotation',
          params: {msg: ann, tag: ann.$$tag},
          callback: sinon.match.func
        })

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
        assert.calledWith(fakeBridge.call, {
          method: 'createAnnotation',
          params: {msg: ann, tag: ann.$$tag},
          callback: sinon.match.func
        })

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
        assert.calledWith(fakeBridge.call, {
          method: 'updateAnnotation',
          params: {msg: ann, tag: ann.$$tag},
          callback: sinon.match.func
        })

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
        assert.calledWith(fakeBridge.call, {
          method: 'deleteAnnotation',
          params: {msg: ann, tag: ann.$$tag},
          callback: sinon.match.func
        })

      it 'parses the result returned by the call', ->
        ann = {id: 1, $$tag: 'tag1'}
        options.parser = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        body = {msg: {}, tag: 'tag1'}
        fakeBridge.call.yieldTo('callback', null, [body])
        assert.called(options.parser)
        assert.calledWith(options.parser, {})

      it 'removes the annotation from the cache on success', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        fakeBridge.call.yieldTo('callback', null, [])
        assert.isUndefined(annSync.cache.tag1)

      it 'does not remove the annotation from the cache if an error occurs', ->
        ann = {id: 1, $$tag: 'tag1'}
        annSync = createAnnotationSync()
        annSync.cache.tag1 = ann
        options.emit('annotationDeleted', ann)

        fakeBridge.call.yieldTo('callback', new Error('Error'), [])
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

        assert.called(fakeBridge.notify)
        assert.calledWith(fakeBridge.notify, {
          method: 'loadAnnotations',
          params: {msg: a, tag: a.$$tag} for a in annotations
        })

      it 'does not send annotations that have already been tagged', ->
        annotations = [{id: 1, $$tag: 'tag1'}, {id: 2, $$tag: 'tag2'}, {id: 3}]
        options.formatter = sinon.spy((x) -> x)
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', annotations)

        assert.called(fakeBridge.notify)
        assert.calledWith(fakeBridge.notify, {
          method: 'loadAnnotations',
          params: [{msg: annotations[2], tag: annotations[2].$$tag}]
        })

      it 'returns early if no annotations are loaded', ->
        annSync = createAnnotationSync()
        options.emit('annotationsLoaded', [])

        assert.notCalled(fakeBridge.notify)
