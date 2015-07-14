uuid = require('node-uuid')

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
  '$scope',
  ($scope) ->
    @container = null
    @collapsed = true
    @parent = null
    @counter = null
    @filter = null

    ###*
    # @ngdoc method
    # @name thread.ThreadController#toggleCollapsed
    # @description
    # Toggle whether or not the replies to this thread are hidden by default.
    # Note that the visibility of replies is also dependent on the state of the
    # thread filter, if present.
    ###
    this.toggleCollapsed = (value) ->
      newval = if value?
                 !!value
               else
                 not @collapsed
      $scope.$broadcast('threadToggleCollapse', value)
      @collapsed = newval

    ###*
    # @ngdoc method
    # @name thread.ThreadController#shouldShowAsReply
    # @description
    # Return a boolean indicating whether this thread should be shown if it is
    # being rendered as a reply to another annotation.
    ###
    this.shouldShowAsReply = ->
      shouldShowUnfiltered = not @parent?.collapsed
      shouldShowFiltered = this._count('match') > 0

      # We always show replies that contain an editor
      if this._count('edit') > 0
        return true

      if this._isFilterActive()
        return shouldShowFiltered
      else
        return shouldShowUnfiltered

    ###*
    # @ngdoc method
    # @name thread.ThreadController#shouldShowNumReplies
    # @description
    # Returns a boolean indicating whether the reply count should be rendered
    # for the annotation at the root of this thread.
    ###
    this.shouldShowNumReplies = ->
      hasChildren = this._count('message') > 0
      allRepliesShown = this._count('message') == this._count('match')
      hasFilterMatch = !this._isFilterActive() || allRepliesShown
      hasChildren && hasFilterMatch

    ###*
    # @ngdoc method
    # @name thread.ThreadController#numReplies
    # @description
    # Returns the cumulative number of replies to the annotation at the root of
    # this thread.
    ###
    this.numReplies = ->
      if @counter
        this._count('message') - 1
      else
        0

    ###*
    # @ngdoc method
    # @name thread.ThreadController#shouldShowLoadMore
    # @description
    # Return a boolean indicating whether the "load more" link should be shown
    # for the annotation at the root of this thread. The "load more" link can be
    # shown when the thread filter is active (although it may not be visible if
    # no replies are hidden in this thread).
    ###
    this.shouldShowLoadMore = ->
      this.container?.message?.id? and this._isFilterActive()

    ###*
    # @ngdoc method
    # @name thread.ThreadController#numLoadMore
    # @description
    # Returns the number of replies in this thread which are currently hidden as
    # a result of the thread filter.
    ###
    this.numLoadMore = ->
      this._count('message') - this._count('match')

    ###*
    # @ngdoc method
    # @name thread.ThreadController#loadMore
    # @description
    # Makes visible any replies in this thread which have been hidden by the
    # thread filter.
    ###
    this.loadMore = ->
      # If we want to show the rest of the replies in the thread, we need to
      # uncollapse all parent threads.
      ctrl = this
      while ctrl
        ctrl.toggleCollapsed(false)
        ctrl = ctrl.parent
      # Deactivate the thread filter for this thread.
      @filter?.active(false)

    ###*
    # @ngdoc method
    # @name thread.ThreadController#matchesFilter
    # @description
    # Returns a boolean indicating whether the annotation at the root of this
    # thread is marked as a match by the current thread filter. If there is no
    # thread filter attached to this thread, it will return true.
    ###
    this.matchesFilter = ->
      if not @filter
        return true
      return @filter.check(@container)

    ###*
    # @ngdoc method
    # @name thread.ThreadController#isNew
    # @description
    # Return true if this is a newly-created annotation (e.g. the user has just
    # created it by clicking the new annotation button in the browser),
    # false otherwise.
    ###
    this.isNew = ->
      return (this.container?.message? and not this.container?.message?.id)

    this._isFilterActive = ->
      if @filter
        @filter.active()
      else
        false

    this._count = (name) ->
      if @counter
        @counter.count(name)
      else
        0

    this.id = uuid.v4()

    this
]


###*
# @ngdoc function
# @name isHiddenThread
# @param {Element} elem An element bound to a ThreadController
# @returns {Boolean} True if the the thread is hidden
###
isHiddenThread = (elem) ->
  parent = elem.parent()
  parentThread = parent.controller('thread')
  if !parentThread
    return false
  return parentThread.collapsed || isHiddenThread(parent)


###*
# @ngdoc directive
# @name thread
# @restrict A
# @description
# Directive that instantiates {@link thread.ThreadController ThreadController}.
###
module.exports = [
  '$parse', '$window', '$location', '$anchorScroll', 'pulse', 'render',
  ($parse,   $window,   $location,   $anchorScroll,   pulse,   render) ->
    linkFn = (scope, elem, attrs, [ctrl, counter, filter]) ->

      # We would ideally use require for this, but searching parents only for a
      # controller is a feature of Angular 1.3 and above only.
      ctrl.parent = elem.parent().controller('thread')
      ctrl.counter = counter
      ctrl.filter = filter

      # If annotation is a reply, it should be uncollapsed so that when
      # shown, replies don't have to be individually expanded.
      if ctrl.parent?
        ctrl.collapsed = false

      # Track the number of messages in the thread
      if counter?
        counter.count 'message', 1
        scope.$on '$destroy', -> counter.count 'message', -1

      # Flash the thread when any child annotations are updated.
      scope.$on 'annotationUpdate', (event) ->
        # If we're hidden, we let the event propagate up to the parent thread.
        if isHiddenThread(elem)
          return
        # Otherwise, stop the event from bubbling, and pulse this thread.
        event.stopPropagation()
        pulse(elem)

      # The watch is necessary because the computed value of the attribute
      # expression may change. This won't happen when we use the thread
      # directive in a repeat, since the element will be torn down whenever the
      # thread might have changed, but we shouldn't assume that here, unless we
      # want to advertise that the thread expression is fixed at link time and
      # should not change.
      scope.$watch $parse(attrs.thread), (thread) ->
        # Queue a render frame to complete the binding and show the element.
        # We call $digest to trigger a scope local update.
        render ->
          ctrl.container = thread
          if ctrl.isNew()
            # Scroll the sidebar to show new annotations.
            $location.hash(ctrl.id)
          scope.$digest()

    controller: ThreadController
    controllerAs: 'vm'
    link: linkFn
    require: ['thread', '?^deepCount', '?^threadFilter']
    scope: true
]
