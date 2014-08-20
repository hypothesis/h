assert = chai.assert

describe 'h.controllers', ->

  beforeEach module('h.controllers')

  describe 'AnnotationViewer', ->
    $scope = null
    annotationViewer = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()
      annotationViewer = $controller 'AnnotationViewerController',
        $scope: $scope

    it 'sets the isEmbedded property to false', ->
      assert.isFalse($scope.isEmbedded)
