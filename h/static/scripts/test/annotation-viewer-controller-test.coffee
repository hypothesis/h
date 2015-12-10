{inject, module} = angular.mock

describe "AnnotationViewerController", ->

  before ->
    angular.module("h", [])
      .controller(
        'AnnotationViewerController',
        require('../annotation-viewer-controller'))

  beforeEach(module("h"))

  # Return the $controller service from Angular.
  getControllerService = ->
    $controller = null
    inject((_$controller_) ->
      $controller = _$controller_
    )
    return $controller

  # Return a new AnnotationViewerController instance.
  createAnnotationViewerController = ({$location, $routeParams, $scope,
                                       streamer, store, streamFilter,
                                       annotationMapper, threading}) ->
    locals = {
      $location: $location or {}
      $routeParams: $routeParams or {id: "test_annotation_id"}
      $scope: $scope or {
        search: {}
        threading: {
          getContainer: ->
        }
      }
      streamer: streamer or {setConfig: ->}
      store: store or {
        AnnotationResource: {get: sinon.spy()}
        SearchResource: {get: sinon.spy()}
      }
      streamFilter: streamFilter or {
        setMatchPolicyIncludeAny: -> {addClause: -> {addClause: ->}}
        getFilter: ->
      }
      annotationMapper: annotationMapper or {loadAnnotations: sinon.spy()}
      threading: threading or {idTable: {}}
    }
    locals["ctrl"] = getControllerService()(
      "AnnotationViewerController", locals)
    return locals

  it "fetches the top-level annotation", ->
    {store} = createAnnotationViewerController({})
    assert.calledOnce(store.AnnotationResource.get)
    assert.calledWith(store.AnnotationResource.get, {id: "test_annotation_id"})

  it "fetches any replies referencing the top-level annotation", ->
    {store} = createAnnotationViewerController({})
    assert.calledOnce(store.SearchResource.get)
    assert.calledWith(store.SearchResource.get, {references: "test_annotation_id"})

  it "loads the top-level annotation and replies into annotationMapper", ->
    {annotationMapper} = createAnnotationViewerController({})

  it "passes the annotations and replies from search into loadAnnotations", ->
    getAnnotation = sinon.stub().callsArgWith(1, {id: 'foo'})
    getReferences = sinon.stub().callsArgWith(1, {rows: [{id: 'bar'}, {id: 'baz'}]})

    {annotationMapper} = createAnnotationViewerController({
      store: {
        AnnotationResource: {get: getAnnotation}
        SearchResource: {get: getReferences}
      }
    })

    assert.calledWith(annotationMapper.loadAnnotations, [{id: 'foo'}])
    assert.calledWith(annotationMapper.loadAnnotations, [{id: 'bar'}, {id: 'baz'}])
