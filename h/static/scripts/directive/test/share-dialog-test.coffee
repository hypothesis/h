{module, inject} = require('angular-mock')

assert = chai.assert

describe 'share-dialog', ->
  $scope = null
  $compile = null
  fakeCrossFrame = null

  before ->
    angular.module('h', [])
    .directive('shareDialog', require('../share-dialog'))

  beforeEach module('h')
  beforeEach module('h.templates')

  beforeEach module ($provide) ->
    fakeCrossFrame = {providers: []}

    $provide.value 'crossframe', fakeCrossFrame
    return

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  it 'generates new via link', ->
    $element = $compile('<div share-dialog="">')($scope)
    fakeCrossFrame.providers.push {entities: ['http://example.com']}
    $scope.$digest()
    assert.equal($scope.viaPageLink,
                 'https://via.hypothes.is/http://example.com')
