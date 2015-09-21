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
  ->
    @container = null
    @collapsed = true
    @parent = null
    @counter = null

    ###*
    # @ngdoc method
    # @name thread.ThreadController#toggleCollapsed
    # @description
    # Toggle whether or not the replies to this thread are hidden by default.
    ###
    this.toggleCollapsed = (value) ->
      newval = if value?
                 !!value
               else
                 not @collapsed
      @collapsed = newval

    ###*
    # @ngdoc method
    # @name thread.ThreadController#shouldShowAsReply
    # @description
    # Return a boolean indicating whether this thread should be shown if it is
    # being rendered as a reply to another annotation.
    ###
    this.shouldShowAsReply = ->
      # We always show replies that contain an editor
      if this._count('edit') > 0
        return true
      return not @parent?.collapsed

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
    # @name thread.ThreadController#isNew
    # @description
    # Return true if this is a newly-created annotation (e.g. the user has just
    # created it by clicking the new annotation button in the browser),
    # false otherwise.
    ###
    this.isNew = ->
      return (this.container?.message? and not this.container?.message?.id)

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
    linkFn = (scope, elem, attrs, [ctrl, counter]) ->

      # We would ideally use require for this, but searching parents only for a
      # controller is a feature of Angular 1.3 and above only.
      ctrl.parent = elem.parent().controller('thread')
      ctrl.counter = counter

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
    require: ['thread', '?^deepCount']
    scope: true
]
