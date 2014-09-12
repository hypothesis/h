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
  '$attrs', '$element', '$parse', '$scope', 'flash', 'render',
  ($attrs,   $element,   $parse,   $scope,   flash,   render) ->
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
      unless @container.message.id
        return flash 'error', 'You must publish this before replying to it.'
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
    # Fire a `threadCollapse` event and toggle the collapsed property
    # unless a listener has called the `preventDefault` method on the event.
    ###
    this.toggleCollapsed = ->
      return if ($scope.$broadcast 'threadCollapse').defaultPrevented
      @collapsed = not @collapsed
      if @collapsed
        $attrs.$addClass(COLLAPSED_CLASS)
      else
        $attrs.$removeClass(COLLAPSED_CLASS)

    ###*
    # @ngdoc method
    # @name thread.ThreadController#toggleShared
    # @description
    # Toggle the shared property.
    ###
    this.toggleShared = ->
      unless @container.message.id
        return flash 'error', 'You must publish this before sharing it.'
      @shared = not @shared
      if @shared
        # Focus and select the share link
        $scope.$evalAsync ->
          $element.find('input').focus().select()

    # Hide the view initially
    $element.hide()

    # Render the view in a future animation frame
    render ->
      vm.container = $parse($attrs.thread)($scope)
      $scope.$digest()
      $element.show()

    # Watch the thread-collapsed attribute.
    if $attrs.threadCollapsed
      $scope.$watch $parse($attrs.threadCollapsed), (collapsed) ->
        vm.toggleCollapsed() if !!collapsed != vm.collapsed

    this
]

###*
# @ngdoc event
# @name thread#threadCollapse
# @eventType broadcast on the current thread scope
# @description
# Broadcast before a thread collapse state is changed. The change can be
# prevented by calling the `preventDefault` method of the event.
###

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
  '$document', '$window',
  ($document,   $window) ->
    linkFn = (scope, elem, attrs, ctrl) ->
      # Toggle collapse on click
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

        # Ignore if the user just activated a form element
        if $document.activeElement is event.target
          return

        scope.$evalAsync ->
          ctrl.toggleCollapsed()

    controller: 'ThreadController'
    controllerAs: 'vm'
    link: linkFn
    scope: true
]


angular.module('h.directives')
.controller('ThreadController', ThreadController)
.directive('thread', thread)
