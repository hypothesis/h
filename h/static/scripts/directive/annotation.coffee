### global -validate ###

# Validate an annotation.
# Annotations must be attributed to a user or marked as deleted.
# A public annotation is valid only if they have a body.
# A non-public annotation requires only a target (e.g. a highlight).
validate = (value) ->
  return unless angular.isObject value
  worldReadable = 'group:__world__' in (value.permissions?.read or [])
  (value.tags?.length or value.text?.length) or
  (value.target?.length and not worldReadable)


# Return an error message based on a server response.
errorMessage = (reason) ->
  if reason.status is 0
    message = "Service unreachable."
  else
    message = reason.status + " " + reason.statusText
    if reason.data.reason
      message = message + ": " + reason.data.reason

  return message


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
# {@link annotationMapper AnnotationMapper service} for persistence.
###
AnnotationController = [
  '$scope', '$timeout', '$q', '$rootScope', '$document',
  'drafts', 'flash', 'permissions', 'tags', 'time',
  'annotationUI', 'annotationMapper', 'session', 'groups'
  ($scope,   $timeout,   $q,   $rootScope,   $document,
   drafts,   flash,   permissions,   tags,   time,
   annotationUI,   annotationMapper,   session,   groups) ->

    @annotation = {}
    @action = 'view'
    @document = null
    @preview = 'no'
    @editing = false
    @embedded = false
    @hasDiff = false
    @showDiff = undefined
    @timestamp = null

    model = $scope.annotationGet()
    if not model.group
      model.group = groups.focused().id

    highlight = model.$highlight
    original = null
    vm = this

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#group.
    # @returns {Object} The full group object associated with the annotation.
    ###
    this.group = ->
      groups.get(model.group)

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#tagsAutoComplete.
    # @returns {Promise} immediately resolved to {string[]} -
    # the tags to show in autocomplete.
    ###
    this.tagsAutoComplete = (query) ->
      $q.when(tags.filter(query))

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
      permissions.isPrivate model.permissions, model.user

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#setPrivate
    #
    # Set permissions on this annotation to private.
    ###
    this.setPrivate = ->
      model.permissions = permissions.private()

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#isShared
    # @returns {boolean} True if the annotation is shared (either with the
    # current group or with everyone).
    ###
    this.isShared = ->
      permissions.isPublic model.permissions, model.group

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#setShared
    #
    # Set permissions on this annotation to share with the current group.
    ###
    this.setShared = ->
      model.permissions = permissions.public(model.group)

    this.setPrivacy = (privacy) ->
      if privacy == 'private'
        this.setPrivate()
      else if privacy == 'shared'
        this.setShared()

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
      # TODO: this should use auth instead of permissions but we might need
      # an auth cache or the JWT -> userid decoding might start to be a
      # performance bottleneck and we would need to get the id token into the
      # session, which we should probably do anyway (and move to opaque bearer
      # tokens for the access token).
      return permissions.permits action, model, session.state.userid

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#delete
    # @description Deletes the annotation.
    ###
    this.delete = ->
      $timeout ->  # Don't use confirm inside the digest cycle
        if confirm "Are you sure you want to delete this annotation?"
          onRejected = (reason) =>
            flash.error(errorMessage(reason), "Deleting annotation failed")
          $scope.$apply ->
            annotationMapper.deleteAnnotation(model).then(null, onRejected)
      , true

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
    # @description Switches the view to a viewer, closing the editor controls
    #              if they are open.
    ###
    this.view = ->
      @editing = false
      @action = 'view'

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#revert
    # @description Reverts an edit in progress and returns to the viewer.
    ###
    this.revert = ->
      drafts.remove model
      if @action is 'create'
        $rootScope.$emit('annotationDeleted', model)
      else
        this.render()
        this.view()

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

    # Update the given annotation domain model object with the data from the
    # given annotation view model object.
    updateDomainModel = (domainModel, viewModel) ->
        angular.extend(
          domainModel, viewModel,
          {tags: (tag.text for tag in viewModel.tags)})

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#save
    # @description Saves any edits and returns to the viewer.
    ###
    this.save = ->
      unless model.user or model.deleted
        return flash.info('Please sign in to save your annotations.')
      unless validate(@annotation)
        return flash.info('Please add text or a tag before publishing.')

      # Update stored tags with the new tags of this annotation
      newTags = @annotation.tags.filter (tag) ->
        tag.text not in (model.tags or [])
      tags.store(newTags)

      switch @action
        when 'create'
          updateDomainModel(model, @annotation)
          onFulfilled = =>
            $rootScope.$emit('annotationCreated', model)
            @view()
          onRejected = (reason) =>
            flash.error(errorMessage(reason), "Saving annotation failed")
          model.$create().then(onFulfilled, onRejected)
        when 'edit'
          updatedModel = angular.copy(model)
          updateDomainModel(updatedModel, @annotation)
          onFulfilled = =>
            angular.copy(updatedModel, model)
            $rootScope.$emit('annotationUpdated', model)
            @view()
          onRejected = (reason) =>
            flash.error(errorMessage(reason), "Saving annotation failed")
          updatedModel.$update(id: updatedModel.id).then(
            onFulfilled, onRejected)


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

      reply = annotationMapper.createAnnotation({references, uri})

      if session.state.userid
        if permissions.isPublic model.permissions
          reply.permissions = permissions.public()
        else
          reply.permissions = permissions.private()

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
      @annotationURI = new URL("/a/#{@annotation.id}", this.baseURI).href

      # Extract the document metadata.
      uri = model.uri
      domain = new URL(uri).hostname
      if model.document
        if uri.indexOf("urn") is 0
          # This URI is not clickable, see if we have something better
          for link in model.document.link when link.href.indexOf("urn")
            uri = link.href
            break

        documentTitle = if Array.isArray(model.document.title)
          model.document.title[0]
        else
          model.document.title

        @document =
          uri: uri
          domain: domain
          title: documentTitle or domain
      else
        @document =
          uri: uri
          domain: domain
          title: domain

      if @document.title.length > 30
        @document.title = @document.title[0..29] + '…'

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
      @timestamp = time.toFuzzyString model.updated
      fuzzyUpdate = time.nextFuzzyUpdate model.updated
      nextUpdate = (1000 * fuzzyUpdate) + 500
      return unless repeat
      $timeout =>
        updateTimestamp(true)
        $scope.$digest()
      , nextUpdate, false

    # Export the baseURI for the share link
    this.baseURI = $document.prop('baseURI')

    # Discard the draft if the scope goes away.
    $scope.$on '$destroy', ->
      updateTimestamp = angular.noop
      drafts.remove model

    # Watch the model.
    # XXX: TODO: don't clobber the view when collaborating
    $scope.$watch (-> model), (model, old) =>
      if model.updated != old.updated
        # Discard saved drafts
        drafts.remove model

        # Propagate an update event up the thread (to pulse changing threads),
        # but only if this is someone else's annotation.
        if model.user != session.state.userid
          $scope.$emit('annotationUpdate')

      # Save highlights once logged in.
      if this.isHighlight() and highlight
        if model.user and not model.id
          model.permissions = permissions.private()
          model.$create().then ->
            $rootScope.$emit('annotationCreated', model)
          highlight = false # Prevents double highlight creation.
        else
          drafts.add model, => this.revert()

      updateTimestamp(model is old)  # repeat on first run
      this.render()
    , true

    # Watch the current user
    # TODO: fire events instead since watchers are not free and auth is rare
    $scope.$watch (-> session.state.userid), (userid) ->
      model.permissions ?= {}
      model.user ?= userid

    # Start editing brand new annotations immediately
    unless model.id? or (this.isHighlight() and highlight) then this.edit()

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
module.exports = [
  '$document',
  ($document) ->
    linkFn = (scope, elem, attrs, [ctrl, thread, threadFilter, counter]) ->
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
        $container = angular.element(event.currentTarget).parent()
        $container.addClass('open').find('input').focus().select()

        # We have to stop propagation here otherwise this click event will
        # re-close the share dialog immediately.
        event.stopPropagation()

        $document.one('click', (event) -> $container.removeClass('open'))
        return

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
            if thread? and threadFilter?
              threadFilter.active(false)
              threadFilter.freeze(true)
          else if old
            counter.count 'edit', -1
            threadFilter?.freeze(false)

        # Clean up when the thread is destroyed
        scope.$on '$destroy', ->
          if ctrl.editing then counter?.count 'edit', -1

    controller: AnnotationController
    controllerAs: 'vm'
    link: linkFn
    require: ['annotation', '?^thread', '?^threadFilter', '?^deepCount']
    scope:
      annotationGet: '&annotation'
      replyCount: '@annotationReplyCount'
      replyCountClick: '&annotationReplyCountClick'
      showReplyCount: '@annotationShowReplyCount'
    templateUrl: 'annotation.html'
]
