class App
  scope:
    frame:
      visible: false
    username: null
    email: null
    password: null
    code: null
    sheet:
      collapsed: true
      tab: 'login'
    personas: []
    persona: null
    token: null

  this.$inject = [
    '$compile', '$element', '$http', '$location', '$scope', '$timeout',
    'annotator', 'drafts', 'flash'
  ]
  constructor: (
    $compile, $element, $http, $location, $scope, $timeout
    annotator, drafts, flash
  ) ->
    {plugins, provider} = annotator
    heatmap = annotator.plugins.Heatmap
    dynamicBucket = true

    heatmap.element.bind 'click', =>
      return unless drafts.discard()
      $location.search('id', null).replace()
      dynamicBucket = true
      annotator.showViewer()
      heatmap.publish 'updated'
      $scope.$digest()

    heatmap.subscribe 'updated', =>
      elem = d3.select(heatmap.element[0])
      data = {highlights, offset} = elem.datum()
      tabs = elem.selectAll('div').data data
      height = $(window).outerHeight(true)
      pad = height * .2

      {highlights, offset} = elem.datum()

      visible = $scope.frame.visible
      if dynamicBucket and visible and $location.path() == '/viewer'
        bottom = offset + heatmap.element.height()
        annotations = highlights.reduce (acc, hl) =>
          if hl.offset.top >= offset and hl.offset.top <= bottom
            if hl.data not in acc
              acc.push hl.data
          acc
        , []
        annotator.showViewer annotations

      elem.selectAll('.heatmap-pointer')
        # Creates highlights corresponding bucket when mouse is hovered
        .on 'mousemove', (bucket) =>
          unless $location.path() == '/viewer' and $location.search()?.id?
            provider.notify
              method: 'setActiveHighlights'
              params: heatmap.buckets[bucket]?.map (a) => a.$$tag

        # Gets rid of them after
        .on 'mouseout', =>
          if $location.path() == '/viewer' and not $location.search()?.id?
            provider.notify method: 'setActiveHighlights'

        # Does one of a few things when a tab is clicked depending on type
        .on 'click', (bucket) =>
          d3.event.stopPropagation()

          # If it's the upper tab, scroll to next bucket above
          if heatmap.isUpper bucket
            threshold = offset + heatmap.index[0]
            next = highlights.reduce (next, hl) ->
              if next < hl.offset.top < threshold then hl.offset.top else next
            , 0
            provider.notify method: 'scrollTop', params: next - pad

          # If it's the lower tab, scroll to next bucket below
          else if heatmap.isLower bucket
            threshold = offset + heatmap.index[0] + pad
            next = highlights.reduce (next, hl) ->
              if threshold < hl.offset.top < next then hl.offset.top else next
            , Number.MAX_VALUE
            provider.notify method: 'scrollTop', params: next - pad

          # If it's neither of the above, load the bucket into the viewer
          else
            return unless drafts.discard()
            dynamicBucket = false
            $location.search('id', null)
            annotator.showViewer heatmap.buckets[bucket]
            $scope.$digest()

    $scope.submit = (form) ->
      return unless form.$valid
      params = for name, control of form when control.$modelValue?
        [name, control.$modelValue]
      params.push ['__formid__', form.$name]
      data = (((p.map encodeURIComponent).join '=') for p in params).join '&'

      $http.post '', data,
        headers:
          'Content-Type': 'application/x-www-form-urlencoded'
        withCredentials: true
      .success (data) =>
        if data.model? then angular.extend $scope, data.model
        if data.flash? then flash q, msgs for q, msgs of data.flash
        if data.status is 'failure' then flash 'error', data.reason
        if data.status is 'okay' then $scope.sheet.collapsed = true

    $scope.$watch 'personas', (newValue, oldValue) =>
      if newValue?.length
        annotator.element.find('#persona')
          .off('change').on('change', -> $(this).submit())
          .off('click')
      else
        $scope.persona = null
        $scope.token = null

    $scope.$watch 'persona', (newValue, oldValue) =>
      if oldValue? and not newValue?
        # TODO: better knowledge of routes
        $http.post '/app/logout', '',
          withCredentials: true
        .success (data) =>
          $scope.$broadcast '$reset'
          if data.model? then angular.extend($scope, data.model)
          if data.flash? then flash q, msgs for q, msgs of data.flash

    $scope.$watch 'token', (newValue, oldValue) =>
      if plugins.Auth?
        plugins.Auth.token = newValue
        plugins.Auth.updateHeaders()

      if newValue?
        if not plugins.Auth?
          annotator.addPlugin 'Auth',
            tokenUrl: $scope.tokenUrl
            token: newValue
        else
          plugins.Auth.setToken(newValue)
        plugins.Auth.withToken plugins.Permissions._setAuthFromToken
      else
        plugins.Permissions.setUser(null)
        delete plugins.Auth

      if annotator.plugins.Store?
        $scope.$root.annotations = []
        annotator.threading.thread []
        annotations = annotator.plugins.Store.annotations
        annotator.plugins.Store.annotations = []
        annotator.deleteAnnotation a for a in annotations
        annotator.plugins.Store.pluginInit()
        dynamicBucket = true

    $scope.$watch 'frame.visible', (newValue) ->
      if newValue
        annotator.show()
        annotator.provider.notify method: 'showFrame'
        $element.find('#toolbar').find('.tri').attr('draggable', true)
      else
        annotator.hide()
        annotator.provider.notify method: 'setActiveHighlights'
        annotator.provider.notify method: 'hideFrame'
        $element.find('#toolbar').find('.tri').attr('draggable', false)

    $scope.$on 'back', ->
      return unless drafts.discard()
      if $location.path() == '/viewer' and $location.search()?.id?
        $location.search('id', null).replace()
      else
        annotator.hide()

    $scope.$on 'showAuth', (event, show=true) ->
      angular.extend $scope.sheet,
        collapsed: !show
        tab: 'login'


    $scope.$on '$reset', => angular.extend $scope, @scope

    # Fetch the initial model from the server
    $http.get 'state',
      withCredentials: true
    .success (data) =>
      if data.model? then angular.extend $scope, data.model
      if data.flash? then flash q, msgs for q, msgs of data.flash

    $scope.$broadcast '$reset'

    # Update scope with auto-filled form field values
    $timeout ->
      for i in $element.find('input') when i.value
        $i = angular.element(i)
        $i.triggerHandler('change')
        $i.triggerHandler('input')
    , 200  # We hope this is long enough


class Annotation
  this.$inject = ['$element', '$location', '$scope', 'annotator', 'drafts', '$timeout']
  constructor: ($element, $location, $scope, annotator, drafts, $timeout) ->
    threading = annotator.threading
    $scope.action = 'create'

    $scope.cancel = ->
      $scope.editing = false
      drafts.remove $scope.model.$modelValue

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model.$modelValue
        else
          $scope.model.$modelValue.text = $scope.origText
          $scope.action = 'create'

    $scope.save = ->
      $scope.editing = false
      drafts.remove $scope.model.$modelValue

      switch $scope.action
        when 'create'
          annotator.publish 'annotationCreated', $scope.model.$modelValue
        when 'delete'
          $scope.model.$modelValue.deleted = true
          unless $scope.model.$modelValue.text? 
            $scope.model.$modelValue.text = ''
          annotator.updateAnnotation $scope.model.$modelValue
        else
          annotator.updateAnnotation $scope.model.$modelValue

    $scope.reply = ->
      unless annotator.plugins.Auth? and annotator.plugins.Auth.haveValidToken()
        $scope.$emit 'showAuth', true
        return

      references =
        if $scope.thread.message.references
          [$scope.thread.message.references..., $scope.thread.message.id]
        else
          [$scope.thread.message.id]

      reply = angular.extend annotator.createAnnotation(),
        references: references

      annotator.setupAnnotation reply

    $scope.edit = ->
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.$modelValue.text
      
    $scope.delete = ->
      annotation = $scope.thread.message
      replies = $scope.thread.children?.length or 0

      # We can delete the annotation if it hasn't got any replies or it is
      # private. Otherwise, we ask for a redaction message.
      if replies == 0 or $scope.form.privacy.$viewValue == 'Private'
        # If we're deleting it without asking for a message, confirm first.
        if confirm "Are you sure you want to delete this annotation?"
          annotator.deleteAnnotation annotation
      else
        $scope.action = 'delete'
        $scope.editing = true
        $scope.origText = $scope.model.$modelValue.text
        $scope.model.$modelValue.text = ''

    $scope.authorize = (action) ->
      if $scope.model.$modelValue? and annotator.plugins?.Permissions?
        annotator.plugins.Permissions.authorize action, $scope.model.$modelValue
      else
        true

    $scope.$on '$routeChangeStart', -> $scope.cancel() if $scope.editing
    $scope.$on '$routeUpdate', -> $scope.cancel() if $scope.editing

    $scope.$watch 'model.$modelValue.id', (id) ->
      if id?
        $scope.thread = threading.getContainer id

        # Check if this is a brand new annotation
        annotation = $scope.thread.message
        if annotation? and drafts.contains annotation
          $scope.editing = true

    $scope.$watch 'shared', (newValue) ->
      if newValue and newValue is true
        $timeout -> $element.find('input').focus()
        $timeout -> $element.find('input').select()

        $scope.shared_link = window.location.protocol + '//' +
          window.location.host + '/a/' + $scope.model.$modelValue.id
        $scope.shared = false

    $scope.share = ->
      $scope.shared = not $scope.shared
      $element.find('.share-dialog').slideToggle()


class Editor
  this.$inject = ['$location', '$routeParams', '$scope', 'annotator']
  constructor: ($location, $routeParams, $scope, annotator) ->
    save = ->
      $location.path('/viewer').search('id', $scope.annotation.id).replace()
      annotator.provider.notify method: 'onEditorSubmit'
      annotator.provider.notify method: 'onEditorHide'

    cancel = ->
      $location.path('/viewer').search('id', null).replace()
      annotator.provider.notify method: 'onEditorHide'

    $scope.action = if $routeParams.action? then $routeParams.action else 'create'
    if $scope.action is 'create'
      annotator.subscribe 'annotationCreated', save
      annotator.subscribe 'annotationDeleted', cancel
    else 
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.subscribe 'annotationUpdated', save

    $scope.$on '$destroy', ->
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.unsubscribe 'annotationUpdated', save
      else 
        if $scope.action is 'create'
          annotator.unsubscribe 'annotationCreated', save
          annotator.unsubscribe 'annotationDeleted', cancel


class Viewer
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator'
  ]
  constructor: (
    $location, $routeParams, $scope,
    annotator
  ) ->
    {plugins, provider} = annotator

    listening = false
    refresh = =>
      return unless $scope.frame.visible
      this.refresh $scope, $routeParams, annotator
      if listening
        if $scope.detail
          plugins.Heatmap.unsubscribe 'updated', refresh
          listening = false
      else
        unless $scope.detail
          plugins.Heatmap.subscribe 'updated', refresh
          listening = true

    $scope.showDetail = (annotation) ->
      search = $location.search() or {}
      search.id = annotation.id
      $location.search(search).replace()

    $scope.focus = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      provider.notify method: 'setActiveHighlights', params: highlights

    $scope.$on '$destroy', ->
      if listening then plugins.Heatmap.unsubscribe 'updated', refresh

    $scope.$on '$routeUpdate', refresh

    refresh()

  refresh: ($scope, $routeParams, annotator) =>
    if $routeParams.id? and annotator.threading.idTable[$routeParams.id]?
      $scope.detail = true
      $scope.thread = annotator.threading.getContainer $routeParams.id
      $scope.focus $scope.thread.message?
    else
      $scope.detail = false
      $scope.thread = null
      $scope.focus []


angular.module('h.controllers', [])
  .controller('AppController', App)
  .controller('AnnotationController', Annotation)
  .controller('EditorController', Editor)
  .controller('ViewerController', Viewer)
