assert = chai.assert

describe 'h.controllers', ->
  fakeParams = null

  beforeEach module('h')

  beforeEach module ($provide) ->
    fakeParams = {id: 'test'}
    $provide.value '$routeParams', fakeParams
    return

  describe 'AnnotationViewer', ->
    $scope = null
    annotationViewer = null

    beforeEach inject ($controller, $rootScope) ->
      $scope = $rootScope.$new()
      $scope.search = {}
      annotationViewer = $controller 'AnnotationViewerController',
        $scope: $scope

    it 'sets the isEmbedded property to false', ->
      assert.isFalse($scope.isEmbedded)
