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
# @property {boolean} shared True if the share link is visible.
#
# @description
#
# `AnnotationController` provides an API for the annotation directive. It
# manages the interaction between the domain and view models and uses the
# {@link annotator annotator service} for persistence.
###
AnnotationController = [
  '$scope', 'annotator', 'drafts', 'flash'
  ($scope,   annotator,   drafts,   flash) ->
    @annotation = {}
    @action = 'view'
    @document = null
    @preview = 'no'
    @editing = false
    @embedded = false
    @shared = false

    highlight = annotator.tool is 'highlight'
    model = $scope.annotationGet()
    original = null

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#authorize
    # @param {string} action The action to authorize.
    # @param {string=} principal Defaults to the current user.
    # @returns {boolean} True if the action is authorized for the principal.
    # @description Checks whether the given principal can perform an action
    # on the annotation.
    ###
    this.authorize = (action, principal) ->
      return false unless model?
      return true if 'group:__world__' in (model.permissions?[action] or [])
      annotator.plugins.Permissions?.authorize action, model, principal

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

      this.render()
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

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#toggleShared
    # @description
    # Toggle the shared property.
    ###
    this.toggleShared = ->
      @shared = not @shared

    ###*
    # @ngdoc method
    # @name annotation.AnnotationController#render
    # @description Called to update the view model when the domain model
    # changes. Initializes brand new annotations and
    ###
    this.render = ->
      # Extend the view model with a copy of the domain model.
      # Note that copy is used so that deep properties aren't shared.
      angular.extend @annotation, angular.copy model

      # Extract the document metadata.
      if model.document and model.target.length
        domain = extractURIComponent(model.uri, 'hostname')

        @document =
          uri: model.uri
          domain: domain
          title: model.document.title or domain

        if @document.title.length > 30
          @document.title = @document.title[0..29] + '…'
      else
        @document = null

      # Form the tags for ngTagsInput
      @annotation.tags = ({text} for text in (model.tags or []))

    # Discard the draft if the scope goes away.
    $scope.$on '$destroy', ->
      drafts.remove model

    # Render on updates..l
    $scope.$watch (-> model.updated), (updated) =>
      if updated then drafts.remove model
      this.render()

    # Update once logged in.
    $scope.$watch (-> model.user), (user) =>
      if highlight and not model.references
        if user
          annotator.publish 'annotationCreated', model
        else
          drafts.add model, => this.revert()
      else
        this.render()

    # Start editing brand new annotations immediately
    unless model.id?
      if model.references or not highlight or not model.target.length
        this.edit()

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
annotation = ['annotator', 'documentHelpers', (annotator, documentHelpers) ->
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

    # Save on Shift + Enter.
    elem.on 'keydown', (event) ->
      if event.keyCode == 13 && event.shiftKey
        event.preventDefault()
        scope.$evalAsync ->
          ctrl.save()

    # Focus and select the share link when it becomes available.
    scope.$watch (-> ctrl.shared), (shared) ->
      if shared then scope.$evalAsync ->
        elem.find('input').focus().select()

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

    # Export the baseURI for the share link
    scope.baseURI = documentHelpers.baseURI

  controller: 'AnnotationController'
  controllerAs: 'vm'
  link: linkFn
  require: ['annotation', '?^thread', '?^threadFilter', '?^deepCount']
  scope:
    annotationGet: '&annotation'
  templateUrl: 'annotation.html'
]


angular.module('h.directives')
.controller('AnnotationController', AnnotationController).
directive('annotation', annotation)
