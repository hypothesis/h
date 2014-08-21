imports = [
  'ngSanitize'
  'h.helpers'
  'h.services'
]


# Use an anchor tag to extract specific components within a uri.
extractURIComponent = (uri, component) ->
  unless extractURIComponent.a
    extractURIComponent.a = document.createElement('a')
  extractURIComponent.a.href = uri
  extractURIComponent.a[component]


class Annotation
  this.$inject = [
    '$element', '$location', '$rootScope', '$sce', '$scope', '$timeout',
    '$window',
    'annotator', 'baseURI', 'drafts'
  ]
  constructor: (
     $element,   $location,   $rootScope,   $sce,   $scope,   $timeout,
     $window,
     annotator,   baseURI,   drafts
  ) ->
    model = $scope.model
    {plugins, threading} = annotator

    $scope.action = 'create'
    $scope.editing = false

    if model.document and model.target.length
      uri = model.uri
      if uri.indexOf("urn") is 0
        # This URI is not clickable, see if we have something better
        model.document.link.forEach (x) ->
          href = x.href
          unless href.indexOf("urn") is 0
            # Let's use this instead
            uri = href

      domain = extractURIComponent(uri, 'hostname')

      title = model.document.title or domain
      if title.length > 30
        title = title.slice(0, 30) + '…'

      $scope.document =
        uri: uri
        domain: domain
        title: title

    $scope.cancel = ($event) ->
      $event?.stopPropagation()
      $scope.editing = false
      drafts.remove $scope.model

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model
        else
          $scope.model.text = $scope.origText
          $scope.model.tags = $scope.origTags
          $scope.action = 'create'

    $scope.save = ($event) ->
      $event?.stopPropagation()
      annotation = $scope.model

      # Forbid saving comments without a body (text or tags)
      if annotator.isComment(annotation) and not annotation.text and
      not annotation.tags?.length
        $window.alert "You can not add a comment without adding some text, or at least a tag."
        return

      # Forbid the publishing of annotations
      # without a body (text or tags)
      if $scope.form.privacy.$viewValue is "Public" and
          $scope.action isnt "delete" and
          not annotation.text and not annotation.tags?.length
        $window.alert "You can not make this annotation public without adding some text, or at least a tag."
        return

      $scope.rebuildHighlightText()

      $scope.editing = false
      drafts.remove annotation

      switch $scope.action
        when 'create'
          # First, focus on the newly created annotation
          unless annotator.isReply annotation
            $rootScope.focus annotation, true

          if annotator.isComment(annotation) and
              $rootScope.viewState.view isnt "Comments"
            $rootScope.applyView "Comments"
          else if not annotator.isReply(annotation) and
              $rootScope.viewState.view not in ["Document", "Selection"]
            $rootScope.applyView "Screen"
          annotator.publish 'annotationCreated', annotation
        when 'delete'
          root = $scope.$root.annotations
          root = (a for a in root when a isnt root)
          annotation.deleted = true
          unless annotation.text? then annotation.text = ''
          annotator.updateAnnotation annotation
        else
          annotator.updateAnnotation annotation

    $scope.reply = ($event) ->
      $event?.stopPropagation()
      unless plugins.Auth? and plugins.Auth.haveValidToken()
        $window.alert "In order to reply, you need to sign in."
        return

      references =
        if $scope.thread.message.references
          [$scope.thread.message.references..., $scope.thread.message.id]
        else
          [$scope.thread.message.id]

      reply =
        references: references
        uri: $scope.thread.message.uri

      annotator.publish 'beforeAnnotationCreated', [reply]
      drafts.add reply
      return

    $scope.edit = ($event) ->
      $event?.stopPropagation()
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.text
      $scope.origTags = $scope.model.tags
      drafts.add $scope.model, -> $scope.cancel()
      return

    $scope.delete = ($event) ->
      $event?.stopPropagation()
      replies = $scope.thread.children?.length or 0

      # We can delete the annotation if it hasn't got any replies or it is
      # private. Otherwise, we ask for a redaction message.
      if replies == 0 or $scope.form.privacy.$viewValue is 'Private'
        # If we're deleting it without asking for a message, confirm first.
        if confirm "Are you sure you want to delete this annotation?"
          if $scope.form.privacy.$viewValue is 'Private' and replies
            #Cascade delete its children
            for reply in $scope.thread.flattenChildren()
              if plugins?.Permissions?.authorize 'delete', reply
                annotator.deleteAnnotation reply

          annotator.deleteAnnotation $scope.model
      else
        $scope.action = 'delete'
        $scope.editing = true
        $scope.origText = $scope.model.text
        $scope.origTags = $scope.model.tags
        $scope.model.text = ''
        $scope.model.tags = ''

    $scope.$watch 'editing', -> $scope.$emit 'toggleEditing'

    $scope.$watch 'model.id', (id) ->
      if id?
        $scope.thread = $scope.model.thread

        # Check if this is a brand new annotation
        if drafts.contains $scope.model
          $scope.editing = true

        $scope.shared_link = "#{baseURI}a/#{$scope.model.id}"

    $scope.$watch 'model.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false

    $scope.$watch 'shared', (newValue) ->
      if newValue? is true
        $timeout -> $element.find('input').focus()
        $timeout -> $element.find('input').select()
        $scope.shared = false
        return

    $scope.$watchCollection 'model.thread.children', (newValue=[]) ->
      return unless $scope.model
      replies = (r.message for r in newValue)
      replies = replies.sort(annotator.sortAnnotations).reverse()
      $scope.model.reply_list = replies

    $scope.toggle = ->
      $element.find('.share-dialog').slideToggle()
      return

    $scope.share = ($event) ->
      $event.stopPropagation()
      return if $element.find('.share-dialog').is ":visible"
      $scope.shared = not $scope.shared
      $scope.toggle()
      return

    $scope.rebuildHighlightText = ->
      if annotator.text_regexp?
        $scope.model.highlightText = $scope.model.text
        for regexp in annotator.text_regexp
          $scope.model.highlightText =
            $scope.model.highlightText.replace regexp, annotator.highlighter


annotation = ['$filter', '$parse', 'annotator', ($filter, $parse, annotator) ->
  link: (scope, elem, attrs, controller) ->
    return unless controller?

    scope.embedded = $parse(attrs.annotationEmbedded)() is true

    # Bind shift+enter to save
    elem.bind
      keydown: (e) ->
        if e.keyCode == 13 && e.shiftKey
          scope.save(e)

    scope.addTag = (tag) ->
      scope.model.tags ?= []
      scope.model.tags.push(tag.text)

    scope.removeTag = (tag) ->
      scope.model.tags = scope.model.tags.filter((t) -> t isnt tag.text)
      delete scope.model.tags if scope.model.tags.length is 0

    # Watch for changes
    scope.$watch 'model', (model) ->
      scope.thread = annotator.threading.idTable[model.id]

      scope.auth = {}
      scope.auth.delete =
        if model? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'delete', model
        else
          true
      scope.auth.update =
        if scope.model? and annotator.plugins?.Permissions?
          annotator.plugins.Permissions.authorize 'update', model
        else
          true

      scope.tags = ({text: tag} for tag in scope.model.tags or [])

  controller: 'AnnotationController'
  require: '?ngModel'
  restrict: 'C'
  scope:
    model: '=ngModel'
    mode: '@'
    replies: '@'
  templateUrl: 'annotation.html'
]


angular.module('h.directives.annotation', imports)
.controller('AnnotationController', Annotation)
.directive('annotation', annotation)
