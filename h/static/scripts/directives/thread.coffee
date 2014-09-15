### global -COLLAPSED_CLASS ###

COLLAPSED_CLASS = 'thread-collapsed'

###*
# @ngdoc type
# @name thread.ThreadController
#
# @property {Object} container The thread domain model. An instance of
# `mail.messageContainer`.
# @property {boolean} collapsed True if the thread is collapsed.
# @property {boolean} hover True if the thread is the hover target.
# @property {boolean} shared True if the share link is visible.
#
# @description
# `ThreadController` provides an API for the thread directive to support
# replying and sharing.
###
ThreadController = [
  ->
    @container = null
    @collapsed = false
    @hover = false
    @shared = false

    vm = this

    ###*
    # @ngdoc method
    # @name thread.ThreadController#reply
    # @description
    # Creates a new message in reply to this thread.
    ###
    this.reply = ->
      if @collapsed then this.toggleCollapsed()

      # Extract the references value from this container.
      {id, references, uri} = @container.message
      if typeof(references) == 'string'
        references = [references]
      else
        references = references or []

      # Construct the reply.
      references = [references..., id]
      reply = mail.messageContainer {references, uri}

      # Add the reply to this container.
      @container.addChild(reply)

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
    # @name thread.ThreadController#toggleShared
    # @description
    # Toggle the shared property.
    ###
    this.toggleShared = ->
      @shared = not @shared

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
  '$document', '$parse', '$window', 'render',
  ($document,   $parse,   $window,   render) ->
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

        # Ignore if the user just activated a form element.
        if $document.activeElement is event.target
          return

        # Ignore if edit interactions are present in the view.
        if counter?.count('edit') > 0
          return

        scope.$evalAsync ->
          ctrl.toggleCollapsed()

      # Hide the element initially.
      elem.hide()

      # Queue a render frame to complete the binding and show the element.
      render ->
        ctrl.container = $parse(attrs.thread)(scope)
        if ctrl.container.message? and counter?
          counter.count 'message', 1
          scope.$on '$destroy', -> counter.count 'message', -1
        scope.$digest()
        elem.show()

      # Add and remove the collapsed class when the collapsed property changes.
      scope.$watch (-> ctrl.collapsed), (collapsed) ->
        if collapsed
          attrs.$addClass COLLAPSED_CLASS
        else
          attrs.$removeClass COLLAPSED_CLASS

      # Focus and select the share link when it becomes available.
      scope.$watch (-> ctrl.shared), (shared) ->
        if shared then scope.$evalAsync ->
          elem.find('footer').find('input').focus().select()

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
