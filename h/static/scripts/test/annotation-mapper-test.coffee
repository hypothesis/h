Promise = global.Promise ? require('es6-promise').Promise
{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


describe 'annotationMapper', ->
  sandbox = sinon.sandbox.create()

  $rootScope = null
  fakeStore = null
  fakeThreading = null
  annotationMapper = null

  before ->
    angular.module('h', [])
    .service('annotationMapper', require('../annotation-mapper'))

  beforeEach module('h')
  beforeEach module ($provide) ->

    fakeStore =
      AnnotationResource: sandbox.stub().returns({})
    fakeThreading =
      idTable: {}

    $provide.value('store', fakeStore)
    $provide.value('threading', fakeThreading)
    return

  beforeEach inject (_annotationMapper_, _$rootScope_) ->
    $rootScope = _$rootScope_
    annotationMapper = _annotationMapper_

  afterEach: -> sandbox.restore()

  describe '.loadAnnotations()', ->
    it 'triggers the annotationLoaded event', ->
      sandbox.stub($rootScope, '$emit')
      annotations = [{id: 1}, {id: 2}, {id: 3}]
      annotationMapper.loadAnnotations(annotations)
      assert.called($rootScope.$emit)
      assert.calledWith($rootScope.$emit, 'annotationsLoaded', [{}, {}, {}])

    it 'triggers the annotationUpdated event for each annotation in the threading cache', ->
      sandbox.stub($rootScope, '$emit')
      annotations = [{id: 1}, {id: 2}, {id: 3}]
      cached = {message: {id: 1, $$tag: 'tag1'}}
      fakeThreading.idTable[1] = cached

      annotationMapper.loadAnnotations(annotations)
      assert.called($rootScope.$emit)
      assert.calledWith($rootScope.$emit, 'annotationUpdated', cached.message)

    it 'replaces the properties on the cached annotation with those from the loaded one', ->
      sandbox.stub($rootScope, '$emit')
      annotations = [{id: 1, url: 'http://example.com'}]
      cached = {message: {id: 1, $$tag: 'tag1'}}
      fakeThreading.idTable[1] = cached

      annotationMapper.loadAnnotations(annotations)
      assert.called($rootScope.$emit)
      assert.calledWith($rootScope.$emit, 'annotationUpdated', {
        id: 1
        url: 'http://example.com'
      })

    it 'excludes cached annotations from the annotationLoaded event', ->
      sandbox.stub($rootScope, '$emit')
      annotations = [{id: 1, url: 'http://example.com'}]
      cached = {message: {id: 1, $$tag: 'tag1'}}
      fakeThreading.idTable[1] = cached

      annotationMapper.loadAnnotations(annotations)
      assert.called($rootScope.$emit)
      assert.calledWith($rootScope.$emit, 'annotationsLoaded', [])

  describe '.createAnnotation()', ->
    it 'creates a new annotaton resource', ->
      ann = {}
      fakeStore.AnnotationResource.returns(ann)
      ret = annotationMapper.createAnnotation(ann)
      assert.equal(ret, ann)

    it 'creates a new resource with the new keyword', ->
      ann = {}
      fakeStore.AnnotationResource.returns(ann)
      ret = annotationMapper.createAnnotation()
      assert.calledWithNew(fakeStore.AnnotationResource)

    it 'emits the "beforeAnnotationCreated" event', ->
      sandbox.stub($rootScope, '$emit')
      ann = {}
      fakeStore.AnnotationResource.returns(ann)
      ret = annotationMapper.createAnnotation()
      assert.calledWith($rootScope.$emit, 'beforeAnnotationCreated', ann)

  describe '.deleteAnnotation()', ->
    it 'deletes the annotation on the server', ->
      p = Promise.resolve()
      ann  = {$delete: sandbox.stub().returns(p)}
      annotationMapper.deleteAnnotation(ann)
      assert.called(ann.$delete)

    it 'triggers the "annotationDeleted" event on success', ->
      sandbox.stub($rootScope, '$emit')
      p = Promise.resolve()
      ann  = {$delete: sandbox.stub().returns(p)}
      annotationMapper.deleteAnnotation(ann)

      p.then ->
        assert.called($rootScope.$emit)
        assert.calledWith($rootScope.$emit, 'annotationDeleted', ann)

    it 'does nothing on error', ->
      sandbox.stub($rootScope, '$emit')
      p = Promise.reject()
      ann  = {$delete: sandbox.stub().returns(p)}
      annotationMapper.deleteAnnotation(ann)

      p.catch ->
        assert.notCalled($rootScope.$emit)

    it 'return a promise that resolves to the deleted annotation', ->
      p = Promise.resolve()
      ann  = {$delete: sandbox.stub().returns(p)}
      return annotationMapper.deleteAnnotation(ann).then((value) ->
        assert.equal(value, ann)
      )
