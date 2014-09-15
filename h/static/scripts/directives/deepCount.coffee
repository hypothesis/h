###*
# @ngdoc type
# @name deepCount.DeepCountController
#
# @description
# `DeepCountController` exports a single getter / setter that can be used
# to retrieve and manipulate a set of counters. Changes to these counters
# are bubbled and aggregated by any instances higher up in the DOM. Digests
# are performed from the top down, scheduled during animation frames, and
# debounced for performance.
###
DeepCountController = [
  '$element', '$scope', 'render',
  ($element,   $scope,   render) ->
    counters = {}
    parent = $element.parent().controller('deepCount')

    ###*
    # @ngdoc method
    # @name deepCount.DeepCountController#count
    #
    # @param {string} key An aggregate key.
    # @param {number} delta If provided, the amount by which the aggregate
    # for the given key should be incremented.
    # @return {number} The value of the aggregate for the given key.
    #
    # @description
    # Modify an aggregate when called with an argument and return its current
    # value.
    ###
    this.count = do -> __cancelFrame = null; (key, delta) ->
      if delta is undefined or delta is 0 then return counters[key] or 0
      counters[key] ?= 0
      counters[key] += delta

      unless counters[key] then delete counters[key]

      if parent
        # Bubble updates.
        parent.count key, delta
      else
        # Debounce digests from the top.
        if __cancelFrame then __cancelFrame()
        __cancelFrame = render ->
          $scope.$digest()
          __cancelFrame = null

      counters[key] or 0

    this
]



###*
# @ngdoc directive
# @name deepCount
# @restrict A
# @description
# Directive that instantiates
# {@link deepCount.DeepCountController DeepCountController} and exports it
# to the current scope under the name specified by the attribute parameter.
###
deepCount = [
  '$parse',
  ($parse) ->
    controller: 'DeepCountController'
    link: (scope, elem, attrs, ctrl) ->
      parsedCounterName = $parse attrs.deepCount
      if parsedCounterName.assign
        parsedCounterName.assign scope, angular.bind ctrl, ctrl.count
]


angular.module('h.directives')
.controller('DeepCountController', DeepCountController)
.directive('deepCount', deepCount)
