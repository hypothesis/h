### global -extractURIComponent, -validate ###

# Use an anchor tag to extract specific components within a uri.
extractURIComponent = (uri, component) ->
  unless extractURIComponent.a
    extractURIComponent.a = document.createElement('a')
  extractURIComponent.a.href = uri
  extractURIComponent.a[component]


# Validate an annotation.
# Annotations must be attributed to a user or marked as deleted.
# A public annotation is valid only if they have a body.
# A non-public annotation requires only a target (e.g. a highlight).
validate = (value) ->
  return unless angular.isObject value
  worldReadable = 'group:__world__' in (value.permissions?.read or [])
  (value.tags?.length or value.text?.length) or
  (value.target?.length and not worldReadable)


###*
# @ngdoc type
# @name annotation.AnnotationController
#
# @property {Object} annotation The annotation view model.
# @property {Object} document The document metadata view model.
# @property {string} action One of 'view', 'edit', 'create' or 'delete'.
# @property {string} preview If previewing an edit then 'yes', else 'no'.
# @property {boolean} editing True if editing components are shown.
# @property {boolean} embedded True if the annotation is an embedded widget.
#
# @description
#
# `AnnotationController` provides an API for the annotation directive. It
# manages the interaction between the domain and view models and uses the
# {@link annotator annotator service} for persistence.
###
AnnotationController = [
  '$scope', '$timeout',
  'annotator', 'drafts', 'flash', 'documentHelpers', 'timeHelpers',
  ($scope,   $timeout,
   annotator,   drafts,   flash,   documentHelpers,   timeHelpers
  ) ->
    @annotation = {}
    @action = 'view'
    @document = null
    @preview = 'no'
    @editing = false
    @embedded = false
    @hasDiff = false
    @showDiff = undefined
    @timestamp = null

    highlight = annotator.tool is 'highlight'
    model = $scope.annotationGet()
    original = null
    vm = this

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#isComment.
    # @returns {boolean} True if the annotation is a comment.
    ###
    this.isComment = ->
      not (model.target?.length or model.references?.length)

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#isHighlight.
    # @returns {boolean} True if the annotation is a highlight.
    ###
    this.isHighlight = ->
      model.target?.length and not model.references?.length and
      not (model.text or model.deleted or model.tags?.length)

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#isPrivate
    # @returns {boolean} True if the annotation is private to the current user.
    ###
    this.isPrivate = ->
      model.user and angular.equals(model.permissions?.read or [], [model.user])

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#authorize
    # @param {string} action The action to authorize.
    # @returns {boolean} True if the action is authorized for the current user.
    # @description Checks whether the current user can perform an action on
    # the annotation.
    ###
    this.authorize = (action) ->
      return false unless model?
      annotator.plugins.Permissions?.authorize action, model

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#delete
    # @description Deletes the annotation.
    ###
    this.delete = ->
      if confirm "Are you sure you want to delete this annotation?"
        annotator.deleteAnnotation model

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#edit
    # @description Switches the view to an editor.
    ###
    this.edit = ->
      drafts.add model, => this.revert()
      @action = if model.id? then 'edit' else 'create'
      @editing = true
      @preview = 'no'

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#view
    # @description Reverts an edit in progress and returns to the viewer.
    ###
    this.revert = ->
      drafts.remove model
      if @action is 'create'
        annotator.publish 'annotationDeleted', model
      else
        this.render()
        @action = 'view'
        @editing = false

    # Calculates the visual diff flags from the targets
    #
    # hasDiff is set to true is there are any targets with a difference
    # shouldShowDiff is set to true if there are some meaningful differences
    #  - that is, more than just uppercase / lowercase
    diffFromTargets = (targets = []) ->
      hasDiff = targets.some (t) ->
        t.diffHTML?
      shouldShowDiff = hasDiff and targets.some (t) ->
        t.diffHTML? and not t.diffCaseOnly

      {hasDiff, shouldShowDiff}

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#save
    # @description Saves any edits and returns to the viewer.
    ###
    this.save = ->
      unless model.user or model.deleted
        return flash 'info', 'Please sign in to save your annotations.'
      unless validate(@annotation)
        return flash 'info', 'Please add text or a tag before publishing.'

      angular.extend model, @annotation,
        tags: (tag.text for tag in @annotation.tags)

      switch @action
        when 'create'
          annotator.publish 'annotationCreated', model
        when 'delete', 'edit'
          annotator.publish 'annotationUpdated', model

      @editing = false
      @action = 'view'

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#reply
    # @description
    # Creates a new message in reply to this annotation.
    ###
    this.reply = ->
      # Extract the references value from this container.
      {id, references, uri} = model
      references = references or []
      if typeof(references) == 'string' then references = [references]

      # Construct the reply.
      references = [references..., id]

      reply = {references, uri}
      annotator.publish 'beforeAnnotationCreated', reply

      reply.permissions.update = [model.user]
      reply.permissions.delete = [model.user]
      reply.permissions.admin = [model.user]

      # If replying to a public annotation make the response public.
      if 'group:__world__' in (model.permissions.read or [])
        reply.permissions.read = ['group:__world__']
      else
        reply.permissions.read = [model.user]

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#render
    # @description Called to update the view when the model changes.
    ###
    this.render = ->
      # Extend the view model with a copy of the domain model.
      # Note that copy is used so that deep properties aren't shared.
      angular.extend @annotation, angular.copy model

      # Set the URI
      @annotationURI = documentHelpers.absoluteURI("/a/#{@annotation.id}")

      # Extract the document metadata.
      if model.document
        uri = model.uri
        if uri.indexOf("urn") is 0
          # This URI is not clickable, see if we have something better
          for link in model.document.link when link.href.indexOf("urn")
            uri = link.href
            break

        domain = extractURIComponent(uri, 'hostname')
        documentTitle = if Array.isArray(model.document.title)
          model.document.title[0]
        else
          model.document.title

        @document =
          uri: uri
          domain: domain
          title: documentTitle or domain

        if @document.title.length > 30
          @document.title = @document.title[0..29] + '…'
      else
        @document = null

      # Form the tags for ngTagsInput.
      @annotation.tags = ({text} for text in (model.tags or []))

      # Calculate the visual diff flags
      diffFlags = diffFromTargets(@annotation.target)
      @hasDiff = diffFlags.hasDiff
      if @hasDiff
        # We don't want to override the showDiff value manually changed
        # by the user, that's why we use a conditional assignment here,
        # instead of directly setting showDiff to the calculated value
        @showDiff ?= diffFlags.shouldShowDiff
      else
        @showDiff = undefined

    updateTimestamp = (repeat=false) =>
      @timestamp = timeHelpers.toFuzzyString model.updated
      fuzzyUpdate = timeHelpers.nextFuzzyUpdate model.updated
      fuzzyUpdate = 5 if fuzzyUpdate < 5  # minimum 5 seconds
      nextUpdate = (1000 * fuzzyUpdate) + 500
      return unless repeat
      $timeout =>
        updateTimestamp(true)
        $scope.$digest()
      , nextUpdate, false

    # Export the baseURI for the share link
    this.baseURI = documentHelpers.baseURI

    # Discard the draft if the scope goes away.
    $scope.$on '$destroy', ->
      updateTimestamp = angular.noop
      drafts.remove model

    # Watch the model.
    # XXX: TODO: don't clobber the view when collaborating
    $scope.$watch (-> model), (model, old) =>
      # Discard saved drafts
      if model.updated != old.updated
        drafts.remove model

      # Save highlights once logged in.
      if highlight and this.isHighlight()
        if model.user
          model.permissions.read = [model.user]
          model.permissions.update = [model.user]
          model.permissions.delete = [model.user]
          model.permissions.admin = [model.user]
          annotator.publish 'annotationCreated', model
          highlight = false  # skip this on future updates
        else
          drafts.add model, => this.revert()

      updateTimestamp(model is old)  # repeat on first run
      this.render()
    , true

    # Start editing brand new annotations immediately
    unless model.id? or (highlight and this.isHighlight()) then this.edit()

    this
]


###*
# @ngdoc directive
# @name annotation
# @restrict A
# @description
# Directive that instantiates
# {@link annotation.AnnotationController AnnotationController}.
#
# If the `annotation-embbedded` attribute is specified, its interpolated
# value is used to signal whether the annotation is being displayed inside
# an embedded widget.
###
annotation = [
  '$document', 'annotator',
  ($document,   annotator) ->
    linkFn = (scope, elem, attrs, [ctrl, thread, threadFilter, counter]) ->
      # Helper function to remove the temporary thread created for a new reply.
      prune = (message) ->
        return if message.id?  # threading plugin will take care of it
        return unless thread.container.message is message
        thread.container.parent?.removeChild(thread.container)

      if thread?
        annotator.subscribe 'annotationDeleted', prune
        scope.$on '$destroy', ->
          annotator.unsubscribe 'annotationDeleted', prune

      # Observe the embedded attribute
      attrs.$observe 'annotationEmbedded', (value) ->
        ctrl.embedded = value? and value != 'false'

      # Save on Meta + Enter or Ctrl + Enter.
      elem.on 'keydown', (event) ->
        if event.keyCode == 13 and (event.metaKey or event.ctrlKey)
          event.preventDefault()
          scope.$evalAsync ->
            ctrl.save()

      scope.share = (event) ->
        scope.$evalAsync ->
          $container = angular.element(event.target).parent()
          $container.addClass('open').find('input').focus().select()
          $document.one('click', (event) -> $container.removeClass('open'))

      # Keep track of edits going on in the thread.
      if counter?
        # Expand the thread if descendants are editing.
        scope.$watch (-> counter.count 'edit'), (count) ->
          if count and not ctrl.editing and thread.collapsed
            thread.toggleCollapsed()

        # Propagate changes through the counters.
        scope.$watch (-> ctrl.editing), (editing, old) ->
          if editing
            counter.count 'edit', 1
            # Disable the filter and freeze it to always match while editing.
            threadFilter?.freeze()
          else if old
            counter.count 'edit', -1
            threadFilter?.freeze(false)

        # Clean up when the thread is destroyed
        scope.$on '$destroy', ->
          if ctrl.editing then counter?.count 'edit', -1

    controller: 'AnnotationController'
    controllerAs: 'vm'
    link: linkFn
    require: ['annotation', '?^thread', '?^threadFilter', '?^deepCount']
    scope:
      annotationGet: '&annotation'
    templateUrl: 'annotation.html'
]


angular.module('h')
.controller('AnnotationController', AnnotationController)
.directive('annotation', annotation)
