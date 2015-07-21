{inject, module} = require('angular-mock')

assert = chai.assert

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
                                       annotationMapper}) ->
    locals = {
      $location: $location or {}
      $routeParams: $routeParams or {id: "test_annotation_id"}
      $scope: $scope or {search: {}}
      streamer: streamer or {send: ->}
      store: store or {
        AnnotationResource: {read: ->},
        SearchResource: {get: ->}}
      streamFilter: streamFilter or {
        setMatchPolicyIncludeAny: -> {addClause: -> {addClause: ->}}
        getFilter: ->
      }
      annotationMapper: annotationMapper or {}
    }
    locals["ctrl"] = getControllerService()(
      "AnnotationViewerController", locals)
    return locals

  it "sets the isEmbedded property to false", ->
    {$scope} = createAnnotationViewerController({})
    assert.isFalse($scope.isEmbedded)
