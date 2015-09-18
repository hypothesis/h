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
      $scope: $scope or {search: {}}
      streamer: streamer or {send: ->}
      store: store or {
        AnnotationResource: {read: sinon.spy()},
        SearchResource: {get: ->}}
      streamFilter: streamFilter or {
        setMatchPolicyIncludeAny: -> {addClause: -> {addClause: ->}}
        getFilter: ->
      }
      threading: sinon.stub()
      annotationMapper: annotationMapper or {loadAnnotations: sinon.spy()}
    }
    locals["ctrl"] = getControllerService()(
      "AnnotationViewerController", locals)
    return locals

  it "calls the annotation API to get the annotation", ->
    {store} = createAnnotationViewerController({})
    assert store.AnnotationResource.read.args[0][0].id == "test_annotation_id"
