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
        SearchResource: {get: sinon.spy()}}
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

  it "calls the search API to get the annotation and its replies", ->
    {store} = createAnnotationViewerController({})
    assert store.SearchResource.get.calledOnce
    assert store.SearchResource.get.calledWith(
      {_id: "test_annotation_id", _separate_replies: true})

  it "passes the annotations and replies from search into loadAnnotations", ->
    {annotationMapper} = createAnnotationViewerController({
      store: {
        SearchResource: {
          # SearchResource.get(id, func) takes an annotation id and a function
          # that it should call with the search result. Our mock .get() here
          # just immediately calls the function with some fake results.
          get: (id, func) ->
            func(
              {
                # In production these would be annotation objects, not strings.
                rows: ['annotation_1', 'annotation_2']
                replies: ['reply_1', 'reply_2', 'reply_3']
              }
            )
        }
      }
    })

    assert annotationMapper.loadAnnotations.calledWith(
        ['annotation_1', 'annotation_2'], ['reply_1', 'reply_2', 'reply_3']
    ), "It should pass all the annotations and replies to loadAnnotations()"
