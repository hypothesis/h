{module, inject} = angular.mock

describe 'store', ->
  $httpBackend = null
  sandbox = null
  store = null
  fakeDocument = null

  before ->
    angular.module('h', ['ngResource'])
    .service('store', require('../store'))

  beforeEach module('h')

  beforeEach module ($provide) ->
    sandbox = sinon.sandbox.create()

    link = document.createElement("link")
    link.rel = 'service'
    link.type = 'application/annotatorsvc+json'
    link.href = 'http://example.com/api'

    fakeDocument = {
      find: sandbox.stub().returns($(link))
    }

    $provide.value '$document', fakeDocument

    return

  afterEach ->
    sandbox.restore()

  beforeEach inject ($q, _$httpBackend_, _store_) ->
    $httpBackend = _$httpBackend_
    store = _store_

    $httpBackend.expectGET('http://example.com/api').respond
      links:
         annotation:
           create: {
             method: 'POST'
             url: 'http://example.com/api/annotations'
           }
           delete: {}
           read: {}
           update: {}
         search:
           url: 'http://0.0.0.0:5000/api/search'
         beware_dragons:
           url: 'http://0.0.0.0:5000/api/roar'
    $httpBackend.flush()

  it 'reads the operations from the backend', ->
    assert.isFunction(store.AnnotationResource, 'expected store.AnnotationResource to be a function')
    assert.isFunction(store.BewareDragonsResource, 'expected store.BewareDragonsResource to be a function')
    assert.isFunction(store.SearchResource, 'expected store.SearchResource to be a function')

  it 'saves a new annotation', ->
    annotation = { id: 'test'}
    annotation = new store.AnnotationResource(annotation)
    saved = {}

    annotation.$create().then ->
      assert.isNotNull(saved.id)

    $httpBackend.expectPOST('http://example.com/api/annotations', annotation).respond ->
      saved.id = annotation.id
      return [201, {}, {}]
    $httpBackend.flush()
