{module, inject} = angular.mock

describe 'h:directives.status-button', ->
  $scope = null
  $compile = null
  $element = null

  before ->
    angular.module('h', [])
    .directive('statusButton', require('../status-button'))

  beforeEach module('h')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  beforeEach ->
    template = '''
    <button status-button="test">Test Button</button>
    '''

    $element = $compile(angular.element(template))($scope).next()

  it 'wraps the button with status labels', ->
    assert.include($element.prop('className'), 'btn-with-message')
    assert.equal($element.find('.btn-message-loading').length, 1)
    assert.equal($element.find('.btn-message-success').length, 1)

  it 'sets the status-button-state attribute when a loading event is triggered', ->
    $scope.$emit('formState', 'test', 'loading')
    assert.equal($element.attr('status-button-state'), 'loading')

  it 'sets the status-button-state attribute when a success event is triggered', ->
    $scope.$emit('formState', 'test', 'success')
    assert.equal($element.attr('status-button-state'), 'success')

  it 'unsets the status-button-state attribute when another event is triggered', ->
    $scope.$emit('formState', 'test', 'reset')
    assert.equal($element.attr('status-button-state'), '')
