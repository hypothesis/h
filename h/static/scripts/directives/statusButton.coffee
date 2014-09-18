# Augments a button to provide loading/status flags for asynchronous actions.
#
# Requires that the attribute provide a "target" form name. It will then listen
# to "formState" events on the scope. These events are expected to provide a
# the form name and a status.
#
# Example
#
#   <button status-button="test-form">Submit</button>
statusButton = ->
  STATE_ATTRIBUTE = 'status-button-state'
  STATE_LOADING = 'loading'
  STATE_SUCCESS = 'success'

  template = '''
  <span class="btn-with-message">
    <span class="btn-message btn-message-loading">
      <span class="btn-icon spinner"><span><span></span></span></span>
    </span>
    <span class="btn-message btn-message-success">
      <span class="btn-message-text">Saved!</span> <i class="btn-message-icon icon-checkmark2"></i>
    </span>
  </span>
  '''

  link: (scope, placeholder, attr, ctrl, transclude) ->
    targetForm = attr.statusButton

    unless targetForm
      throw new Error('status-button attribute should provide a form name')

    elem = angular.element(template)
    placeholder.after(elem)
    transclude(scope, (clone) -> elem.append(clone))

    scope.$on 'formState', (event, formName, formState) ->
      return unless formName == targetForm
      unless formState in [STATE_LOADING, STATE_SUCCESS]
        formState = ''
      elem.attr(STATE_ATTRIBUTE, formState)
  transclude: 'element'


angular.module('h.directives').directive('statusButton', statusButton)
