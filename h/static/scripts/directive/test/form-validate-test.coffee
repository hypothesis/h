{module, inject} = angular.mock

describe 'form-validate', ->
  $compile = null
  $element = null
  $scope = null
  controller = null

  before ->
    angular.module('h', [])
    .directive('formValidate', require('../form-validate'))

  beforeEach module('h')
  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

    template = '<form form-validate onsubmit="return false"></form>'
    $element = $compile(angular.element(template))($scope)

    controller = $element.controller('formValidate')

  it 'performs validation and rendering on registered controls on submit', ->
    mockControl =
      '$name': 'babbleflux'
      '$setViewValue': sinon.spy()
      '$render': sinon.spy()

    controller.addControl(mockControl)

    $element.triggerHandler('submit')
    assert.calledOnce(mockControl.$setViewValue)
    assert.calledOnce(mockControl.$render)

    mockControl2 =
      '$name': 'dubbledabble'
      '$setViewValue': sinon.spy()
      '$render': sinon.spy()

    controller.removeControl(mockControl)
    controller.addControl(mockControl2)

    $element.triggerHandler('submit')
    assert.calledOnce(mockControl.$setViewValue)
    assert.calledOnce(mockControl.$render)
    assert.calledOnce(mockControl2.$setViewValue)
    assert.calledOnce(mockControl2.$render)
