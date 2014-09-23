### global -COLLAPSED_CLASS ###

COLLAPSED_CLASS = 'thread-collapsed'

###*
# @ngdoc type
# @name thread.ThreadController
#
# @property {Object} container The thread domain model. An instance of
# `mail.messageContainer`.
# @property {boolean} collapsed True if the thread is collapsed.
#
# @description
# `ThreadController` provides an API for the thread directive controlling
# the collapsing behavior.
###
ThreadController = [
  ->
    @container = null
    @collapsed = false

    ###*
    # @ngdoc method
    # @name thread.ThreadController#toggleCollapsed
    # @description
    # Toggle the collapsed property.
    ###
    this.toggleCollapsed = ->
      @collapsed = not @collapsed

    ###*
    # @ngdoc method
    # @name thread.ThreadController#showReplyToggle
    # @description
    # Determines whether the reply toggle button should be displayed for the
    # current thread.
    ###
    this.showReplyToggle = (messageCount) ->
      messageCount > 1 && !(@collapsed && @container.parent.parent)

    this
]


###*
# @ngdoc directive
# @name thread
# @restrict A
# @description
# Directive that instantiates {@link thread.ThreadController ThreadController}.
#
# If the `thread-collapsed` attribute is specified, it is treated as an
# expression to watch in the context of the current scope that controls
# the collapsed state of the thread.
###
thread = [
  '$parse', '$window', 'render',
  ($parse,   $window,   render) ->
    linkFn = (scope, elem, attrs, [ctrl, counter]) ->
      # Toggle collapse on click.
      elem.on 'click', (event) ->
        event.stopPropagation()

        # Ignore if the target scope has been destroyed.
        # Prevents collapsing when e.g. a child is deleted by a click event.
        if angular.element(event.target).scope() is undefined
          return

        # Ignore if the user just created a non-empty selection.
        sel = $window.getSelection()
        if sel.containsNode(event.target, true) and sel.toString().length
          return

        # Ignore if the user clicked a link
        if event.target.tagName in ['A', 'INPUT']
          return unless angular.element(event.target).hasClass 'reply-count'

        # Ignore a collapse if edit interactions are present in the view.
        if counter?.count('edit') > 0 and not ctrl.collapsed
          return

        scope.$evalAsync ->
          ctrl.toggleCollapsed()

      # Queue a render frame to complete the binding and show the element.
      render ->
        ctrl.container = $parse(attrs.thread)(scope)
        counter.count 'message', 1
        scope.$digest()

      scope.$on '$destroy', -> counter.count 'message', -1

      # Add and remove the collapsed class when the collapsed property changes.
      scope.$watch (-> ctrl.collapsed), (collapsed) ->
        if collapsed
          attrs.$addClass COLLAPSED_CLASS
        else
          attrs.$removeClass COLLAPSED_CLASS

      # Watch the thread-collapsed attribute.
      if attrs.threadCollapsed
        scope.$watch $parse(attrs.threadCollapsed), (collapsed) ->
          ctrl.toggleCollapsed() if !!collapsed != ctrl.collapsed

    controller: 'ThreadController'
    controllerAs: 'vm'
    link: linkFn
    require: ['thread', '?^deepCount']
    scope: true
]


angular.module('h.directives')
.controller('ThreadController', ThreadController)
.directive('thread', thread)
