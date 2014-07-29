assert = chai.assert

describe 'h.directives.statusButton', ->
  $scope = null
  $compile = null
  $element = null

  beforeEach module('h.directives')

  beforeEach inject (_$compile_, _$rootScope_) ->
    $compile = _$compile_
    $scope = _$rootScope_.$new()

  beforeEach ->
    template = '''
    <button status-button="test">Test Button</button>
    '''

    $element = $compile(angular.element(template))($scope)

  it 'wraps the button with status labels', ->
    parent = $element.parent()
    assert.include(parent.prop('className'), 'btn-with-message')

    assert.equal(parent.find('.btn-message-loading').length, 1)
    assert.equal(parent.find('.btn-message-success').length, 1)

  it 'sets the status-button-state attribute when a loading event is triggered', ->
    parent = $element.parent()
    $scope.$emit('form-state', 'test', 'loading')
    assert.equal(parent.attr('status-button-state'), 'loading')

  it 'sets the status-button-state attribute when a success event is triggered', ->
    parent = $element.parent()
    $scope.$emit('form-state', 'test', 'success')
    assert.equal(parent.attr('status-button-state'), 'success')

  it 'unsets the status-button-state attribute when another event is triggered', ->
    parent = $element.parent()
    $scope.$emit('form-state', 'test', 'reset')
    assert.equal(parent.attr('status-button-state'), '')
