### global -validate ###

events = require('../events')

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
# @property {boolean} isSidebar True if we are in the sidebar (not on the
#                               stream page or an individual annotation page)
#
# @description
#
# `AnnotationController` provides an API for the annotation directive. It
# manages the interaction between the domain and view models and uses the
# {@link annotationMapper AnnotationMapper service} for persistence.
###
AnnotationController = [
  '$document', '$q', '$rootScope', '$scope', '$timeout', '$window',
  'annotationUI', 'annotationMapper', 'drafts', 'flash', 'groups',
  'permissions', 'session', 'tags', 'time'
  ($document,   $q,   $rootScope,   $scope,   $timeout,   $window,
   annotationUI,   annotationMapper,   drafts,   flash,   groups,
   permissions,   session,   tags,   time) ->

    # @annotation is the view model, containing the unsaved annotation changes
    @annotation = {}
    @action = 'view'
    @document = null
    @preview = 'no'
    @editing = false
    @isSidebar = false
    @timestamp = null

    # 'model' is the domain model, containing the currently saved version
    # of the annotation
    model = $scope.annotationGet()

    model.user ?= session.state.userid

    # Set the group of new annotations.
    if not model.group
      model.group = groups.focused().id

    # Set the permissions of new annotations.
    model.permissions = model.permissions or permissions.default(model.group)

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
      permissions.isPrivate @annotation.permissions, model.user

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#isShared
    # @returns {boolean} True if the annotation is shared (either with the
    # current group or with everyone).
    ###
    this.isShared = ->
      permissions.isShared @annotation.permissions, model.group

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#setPrivacy
    #
    # Set the privacy settings on the annotation to a predefined
    # level. The supported levels are 'private' which makes the annotation
    # visible only to its creator and 'shared' which makes the annotation
    # visible to everyone in the group.
    #
    # The changes take effect when the annotation is saved
    ###
    this.setPrivacy = (privacy) ->

      # When the user changes the privacy level of an annotation they're
      # creating or editing, we cache that and use the same privacy level the
      # next time they create an annotation.
      # But _don't_ cache it when they change the privacy level of a reply.
      if not model.references  # If the annotation is not a reply.
        permissions.setDefault(privacy)

      if privacy == 'private'
        @annotation.permissions = permissions.private()
      else if privacy == 'shared'
        @annotation.permissions = permissions.shared(model.group)

    ###*
    # @ngdoc method
    # @name annotation.AnnotaitonController#hasContent
    # @returns {boolean} True if the currently edited annotation has
    #          content (ie. is not just a highlight)
    ###
    this.hasContent = ->
      @annotation.text?.length > 0 || @annotation.tags?.length > 0

    ###*
    # @returns {boolean} True if this annotation has quotes
    ###
    this.hasQuotes = ->
      @annotation.target.some (target) ->
        target.selector && target.selector.some (selector) ->
          selector.type == 'TextQuoteSelector'

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
        if $window.confirm "Are you sure you want to delete this annotation?"
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
      if !drafts.get(model)
        updateDraft(model)
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

    # Update the given annotation domain model object with the data from the
    # given annotation view model object.
    updateDomainModel = (domainModel, viewModel) ->
        angular.extend(
          domainModel, viewModel,
          {tags: (tag.text for tag in viewModel.tags)})

    # Create or update the existing draft for this annotation using
    # the text and tags from the domain model in 'draft'
    updateDraft = (draft) ->
      # Drafts only preserve the text, tags and permissions of the annotation
      # (i.e. only the bits that the user can edit), changes to other
      # properties are not preserved.
      drafts.update(model, {
        text: draft.text
        tags: draft.tags
        permissions: draft.permissions
      })

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

      reply.group = model.group

      if session.state.userid
        if permissions.isShared(model.permissions, model.group)
          reply.permissions = permissions.shared(reply.group)
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
      @annotation = angular.extend {}, angular.copy(model)

      # if we have unsaved changes to this annotation, apply them
      # to the view model
      draft = drafts.get(model)
      if draft
        angular.extend @annotation, angular.copy(draft)

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
      @annotation.tags = ({text} for text in (@annotation.tags or []))

    updateTimestamp = (repeat=false) =>
      if not model.updated
        # New (not yet saved to the server) annotations don't have any .updated
        # yet, so we can't update their timestamp.
        return
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

    $scope.$on '$destroy', ->
      updateTimestamp = angular.noop

    # watch for changes to the domain model and recreate the view model
    # when it changes
    # XXX: TODO: don't clobber the view when collaborating
    $scope.$watch (-> model), (model, old) =>
      if model.updated != old.updated
        # Discard saved drafts
        drafts.remove model

      # Save highlights once logged in.
      if this.isHighlight() and highlight
        if model.user and not model.id
          model.permissions = permissions.private()
          model.$create().then ->
            $rootScope.$emit('annotationCreated', model)
          highlight = false # Prevents double highlight creation.
        else
          updateDraft(model)

      updateTimestamp(model is old)  # repeat on first run
      this.render()
    , true

    $scope.$on(events.USER_CHANGED, ->
      model.user ?= session.state.userid

      # Set model.permissions on sign in, if it isn't already set.
      # This is because you can create annotations when signed out and they
      # will have model.permissions = null, then when you sign in we set the
      # permissions correctly here.
      model.permissions = model.permissions or permissions.default(model.group)
    )

    # if this is a new annotation or we have unsaved changes,
    # then start editing immediately
    isNewAnnotation = !(model.id || (this.isHighlight() && highlight));
    if isNewAnnotation || drafts.get(model)
      this.edit()

    # when the current group changes, persist any unsaved changes using
    # the drafts service. They will be restored when this annotation is
    # next loaded.
    $scope.$on events.GROUP_FOCUSED, ->
      if !vm.editing
        return

      # move any new annotations to the currently focused group when
      # switching groups. See GH #2689 for context
      if !model.id
        newGroup = groups.focused().id
        if permissions.isShared(vm.annotation.permissions, vm.annotation.group)
          model.permissions = permissions.shared(newGroup)
          vm.annotation.permissions = model.permissions
        model.group = newGroup
        vm.annotation.group = model.group

      # if we have a draft, update it, otherwise (eg. when the user signs out)
      # do not create a new one
      if drafts.get(model)
        draftDomainModel = {}
        updateDomainModel(draftDomainModel, vm.annotation)
        updateDraft(draftDomainModel)

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
###
module.exports = [
  '$document', 'features'
  ($document,   features) ->
    linkFn = (scope, elem, attrs, [ctrl, thread, threadFilter, counter]) ->
      # Observe the isSidebar attribute
      attrs.$observe 'isSidebar', (value) ->
        ctrl.isSidebar = value? and value != 'false'

      # Save on Meta + Enter or Ctrl + Enter.
      elem.on 'keydown', (event) ->
        if event.keyCode == 13 and (event.metaKey or event.ctrlKey)
          event.preventDefault()
          scope.$evalAsync ->
            ctrl.save()

      # Give template access to feature flags
      scope.feature = features.flagEnabled

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
      # indicates whether this is the last reply in a thread
      isLastReply: '='
      replyCount: '@annotationReplyCount'
      replyCountClick: '&annotationReplyCountClick'
      showReplyCount: '@annotationShowReplyCount'
    templateUrl: 'annotation.html'
]
