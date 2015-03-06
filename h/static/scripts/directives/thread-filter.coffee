###*
# @ngdoc type
# @name threadFilter.ThreadFilterController
#
# @property {boolean} match True if the last checked message was a match.
#
# @description
# `ThreadFilterController` provides an API for maintaining filtering over
# a message thread.
###
ThreadFilterController = [
  'viewFilter'
  (viewFilter) ->
    @match = false

    @_active = false
    @_children = []
    @_filters = null
    @_frozen = false

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#active
    #
    # @param {boolean=} active New state
    # @return {boolean} state
    #
    # @description
    # This method is a getter / setter.
    #
    # Activate or deactivate filtering when called with an argument and
    # return the activation status.
    ###
    this.active = (active) ->
      if active is undefined then return @_active
      else if @active == active then return @_active
      else
        child.active active for child in @_children
        if @_frozen then @_active else @_active = active

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#filters
    #
    # @param {Object=} filters New filters
    # @return {Object} filters
    #
    # @description
    # This method is a getter / setter.
    #
    # Set the filter configuration when called with an argument and return
    # return the configuration.
    ###
    this.filters = (filters) ->
      if filters is undefined then return @_filters
      else if @filters == filters then return @_filters
      else
        child.filters filters for child in @_children
        if @_frozen then @_filters else @_filters = filters

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#freeze
    #
    # @param {boolean=} frozen New state
    # @return {boolean} frozen state
    #
    # @description
    # This method is a getter / setter.
    #
    # Freeze or unfreeze the filter when called with an argument and
    # return the frozen state. A frozen filter will not change its activation
    # state or filter configuration.
    ###
    this.freeze = (frozen=true) ->
      if frozen? then @_frozen = frozen else @_frozen

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#check
    #
    # @param {Object} container The `mail.messageContainer` to filter.
    # @return {boolean} True if the message matches the filters, it has not
    # yet been saved, or if filtering is not active.
    #
    # @description
    # Check whether a message container carries a message matching the
    # configured filters. If filtering is not active then the result is
    # always `true`. Updates the `match` property to reflect the result.
    ###
    this.check = (container) ->
      unless container?.message then return false
      if this.active()
        @match = !!viewFilter.filter([container.message], @_filters).length
      else
        @match = true

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#registerChild
    #
    # @param {Object} target The child controller instance.
    #
    # @description
    # Add another instance of the thread filter controller to the set of
    # registered children. Changes in activation status and filter configuration
    # are propagated to child controllers.
    ###
    this.registerChild = (target) ->
      @_children.push target

    ###*
    # @ngdoc method
    # @name threadFilter.ThreadFilterController#unregisterChild
    #
    # @param {Object} target The child controller instance.
    #
    # @description
    # Remove a previously registered instance of the thread filter controller
    # from the set of registered children.
    ###
    this.unregisterChild = (target) ->
      @_children = (child for child in @_children if child isnt target)

    this
]


###*
# @ngdoc directive
# @name threadFilter
# @restrict A
# @description
# Directive that instantiates
# {@link threadFilter.ThreadFilterController ThreadController}.
#
# The threadFilter directive utilizes the {@link searchfilter searchfilter}
# service to parse the expression passed in the directive attribute as a
# faceted search query and configures its controller with the resulting
# filters. It watches the `match` property of the controller and updates
# its thread's message count under the 'filter' key.
###
threadFilter = [
  '$parse', 'searchfilter'
  ($parse,   searchfilter) ->
    linkFn = (scope, elem, attrs, [ctrl, counter]) ->
      if counter?
        scope.$watch (-> ctrl.match), (match, old) ->
          if match and not old
            counter.count 'match', 1
          else if old
            counter.count 'match', -1

        scope.$on '$destroy', ->
          if ctrl.match then counter.count 'match', -1

      if parentCtrl = elem.parent().controller('threadFilter')
        ctrl.filters parentCtrl.filters()
        ctrl.active parentCtrl.active()
        parentCtrl.registerChild ctrl
        scope.$on '$destroy', -> parentCtrl.unregisterChild ctrl
      else
        scope.$watch $parse(attrs.threadFilter), (query) ->
          unless query then return ctrl.active false
          filters = searchfilter.generateFacetedFilter(query)
          ctrl.filters filters
          ctrl.active true

    controller: 'ThreadFilterController'
    controllerAs: 'threadFilter'
    link: linkFn
    require: ['threadFilter', '?^deepCount']
]


angular.module('h')
.controller('ThreadFilterController', ThreadFilterController)
.directive('threadFilter', threadFilter)
