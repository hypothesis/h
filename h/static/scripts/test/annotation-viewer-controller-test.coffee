{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose assert, prefix: null


describe 'AnnotationViewerController', ->
  annotationViewerController = null

  before ->
    angular.module('h', ['ngRoute'])
    .controller('AnnotationViewerController', require('../annotation-viewer-controller'))

  beforeEach inject ($controller, $rootScope) ->
    $scope = $rootScope.$new()
    $scope.search = {}
    annotationViewerController = $controller 'AnnotationViewerController',
      $scope: $scope

    it 'sets the isEmbedded property to false', ->
      assert.isFalse($scope.isEmbedded)
