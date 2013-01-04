class App
  scope:
    sheet:
      collapsed: true
      tab: 'login'
    personas: []
    persona: null
    token: null

  this.$inject = [
    '$compile', '$element', '$http', '$location', '$scope',
    'annotator', 'threading'
  ]
  constructor: (
    $compile, $element, $http, $location, $scope,
    annotator, threading
    ) ->
    $scope.reset = => angular.extend $scope, @scope

    {plugins, provider} = annotator
    heatmap = annotator.plugins.Heatmap
    heatmap.element.appendTo $element

    # Update the heatmap when the host is updated or annotations are loaded
    events  = ['hostUpdated', 'annotationsLoaded']
    for event in events
      annotator.subscribe event, ->
        provider.getHighlights ({highlights, offset}) ->
          $scope.$apply ->
            heatmap.updateHeatmap
              highlights: highlights.map (hl) ->
                thread = (threading.getContainer hl.data.id)
                hl.data = thread.message?.annotation
                hl
              offset: offset

    heatmap.subscribe 'updated', =>
      tabs = d3.select(annotator.element[0])
        .selectAll('div.heatmap-pointer')
        .data =>
          buckets = []
          heatmap.index.forEach (b, i) =>
            if heatmap.buckets[i].length > 0
              buckets.push i
            else if heatmap.isUpper(i) or heatmap.isLower(i)
              buckets.push i
          buckets

      heatmap.element.bind 'click', ->
        $scope.$apply -> $location.path('/viewer').search(null).replace()
        annotator.show()

      {highlights, offset} = d3.select(heatmap.element[0]).datum()
      height = $(window).outerHeight(true)
      pad = height * .2

      # Enters into tabs var, and generates bucket pointers from them
      tabs.enter().append('div')
        .classed('heatmap-pointer', true)

      tabs.exit().remove()

      tabs

        .style 'top', (d) =>
          "#{(heatmap.index[d] + heatmap.index[d+1]) / 2}px"

        .html (d) =>
          "<div class='label'>#{heatmap.buckets[d].length}</div><div class='svg'></div>"

        .classed('upper', heatmap.isUpper)
        .classed('lower', heatmap.isLower)

        .style 'display', (d) =>
          if (heatmap.buckets[d].length is 0) then 'none' else ''

        # Creates highlights corresponding bucket when mouse is hovered
        .on 'mousemove', (bucket) =>
          unless $location.path() == '/viewer' and $location.search()?.id?
            provider.setActiveHighlights heatmap.buckets[bucket]?.map (a) =>
              a.id

        # Gets rid of them after
        .on 'mouseout', =>
          if $location.path() == '/viewer'
            unless $location.search()?.id?
              bucket = heatmap.buckets[$location.search()?.bucket]
              provider.setActiveHighlights bucket?.map (a) => a.id
          else
            provider.setActiveHighlights null

        # Does one of a few things when a tab is clicked depending on type
        .on 'mouseup', (bucket) =>
          d3.event.preventDefault()
          search = $location.search() or {}
          search.bucket = bucket

          # If it's the upper tab, scroll to next bucket above
          if heatmap.isUpper bucket
            threshold = offset + heatmap.index[0]
            next = highlights.reduce (next, hl) ->
              if next < hl.offset.top < threshold then hl.offset.top else next
            , threshold - height
            provider.scrollTop next - pad
            delete search.bucket

          # If it's the lower tab, scroll to next bucket below
          else if heatmap.isLower bucket
            threshold = offset + heatmap.index[0] + pad
            next = highlights.reduce (next, hl) ->
              if threshold < hl.offset.top < next then hl.offset.top else next
            , offset + height
            provider.scrollTop next - pad
            delete search.bucket

          # If it's neither of the above, load the bucket into the viewer
          else
            delete search.id
            annotator.show()

          $scope.$apply -> $location.path('/viewer').search(search).replace()

    $scope.submit = (form) ->
      params = for name, control of form when control.$modelValue?
        [name, control.$modelValue]
      params.push ['__formid__', form.$name]
      data = (((p.map encodeURIComponent).join '=') for p in params).join '&'

      $http.post '', data,
        headers:
          'Content-Type': 'application/x-www-form-urlencoded'
        withCredentials: true
      .success (data) =>
        # Extend the scope with updated model data
        angular.extend($scope, data.model) if data.model?
        # TODO: flash data.error server messages

    $scope.toggleShow = ->
      if annotator.visible
        $location.path('').replace()
        annotator.hide()
      else
        if $location.path()?.match '^/?$'
          $location.path('/viewer').replace()
        annotator.show()

    $scope.$watch 'personas', (newValue, oldValue) =>
      if newValue?.length
        annotator.element.find('#persona')
          .off('change').on('change', -> $(this).submit())
          .off('click')
        $scope.sheet.collapsed = true
      else
        $scope.persona = null
        $scope.token = null

    $scope.$watch 'persona', (newValue, oldValue) =>
      if oldValue? and not newValue?
        $http.post 'logout', '',
          withCredentials: true
        .success (data) => $scope.reset()

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
        plugins.Auth.withToken plugins.HypothesisPermissions._setAuthFromToken
      else
        plugins.HypothesisPermissions.setUser(null)
        delete plugins.Auth

    $scope.$on 'showAuth', (event, show=true) ->
      angular.extend $scope.sheet,
        collapsed: !show
        tab: 'login'

    # Fetch the initial model from the server
    $http.get 'model',
      withCredentials: true
    .success (data) =>
      angular.extend $scope, data

    $scope.$evalAsync 'reset()'


class Annotation
  this.$inject = [
    '$element', '$scope', '$rootScope', '$timeout',
    'annotator', 'threading'
  ]
  constructor: (
    $element, $scope, $rootScope, $timeout
    annotator, threading
  ) ->
    $scope.cancel = ->
      $scope.editing = false
      if $scope.$modelValue.draft
        annotator.publish 'annotationDeleted', $scope.$modelValue

    $scope.save = ->
      $scope.editing = false
      $scope.$modelValue.draft = false
      if $scope.edited
        annotator.publish 'annotationUpdated', $scope.$modelValue
      else
        annotator.publish 'annotationCreated', $scope.$modelValue

    $scope.reply = ->
      unless annotator.plugins.Auth.haveValidToken()
        $rootScope.$broadcast 'showAuth', true
        return
      reply = annotator.createAnnotation()
      Object.defineProperty reply, 'draft',
        value: true
        writable: true
      if $scope.$modelValue.thread
        references = [$scope.$modelValue.thread, $scope.$modelValue.id]
      else
        references = [$scope.$modelValue.id]
      reply.thread = references.join '/'
      parentThread = (threading.getContainer $scope.$modelValue.id)
      replyThread = (threading.getContainer reply.id)
      replyThread.message =
        annotation: reply
        id: reply.id
        references: references
      parentThread.addChild replyThread

    $scope.$watch '$modelValue.draft', (newValue) ->
      $scope.editing = newValue
      if newValue then $timeout -> $element.find('textarea').focus()

class Editor
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator', 'threading'
  ]
  constructor: (
    $location, $routeParams, $scope,
    annotator, threading
  ) ->
    save = ->
      $location.path('/viewer').replace()
      annotator.provider.onEditorSubmit()
      annotator.provider.onEditorHide()

    cancel = ->
      search = $location.search() or {}
      delete search.id
      $location.path('/viewer').search(search).replace()
      annotator.provider.onEditorHide()

    annotator.subscribe 'annotationCreated', save
    annotator.subscribe 'annotationDeleted', cancel

    $scope.$on '$destroy', ->
      annotator.unsubscribe 'annotationCreated', save
      annotator.unsubscribe 'annotationDeleted', cancel

    thread = (threading.getContainer $routeParams.id)
    annotation = thread.message?.annotation
    if annotation?
      annotation.draft = true
      $scope.annotation = annotation


class Viewer
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator', 'threading'
  ]
  constructor: (
    $location, $routeParams, $scope,
    annotator, threading
  ) ->
    {plugins, provider} = annotator

    listening = false
    refresh = =>
      this.refresh $scope, $routeParams, threading, plugins.Heatmap
      if listening
        if $scope.detail or $routeParams.bucket?
          plugins.Heatmap.unsubscribe 'updated', refresh
          listening = false
      else
        unless $scope.detail or $routeParams.bucket?
          plugins.Heatmap.subscribe 'updated', refresh
          listening = true

    $scope.annotations = []
    $scope.detail = false
    $scope.thread = null

    $scope.showDetail = (annotation) ->
      search = $location.search() or {}
      search.id = annotation.id
      $location.search(search).replace()

    $scope.focus = (annotation=$scope.annotations) ->
      if $routeParams.id?
        highlights = [$routeParams.id]
      else if angular.isArray annotation
        highlights = (a.id for a in annotation)
      else if angular.isObject annotation
        highlights = [annotation.id]
      else
        highlights = []
      provider.setActiveHighlights highlights

    $scope.$on '$destroy', ->
      if listening then plugins.Heatmap.unsubscribe 'updated', refresh

    $scope.$on '$routeUpdate', refresh

    refresh()

  refresh: ($scope, $routeParams, threading, heatmap) =>
    if $routeParams.id?
      $scope.detail = true
      $scope.thread = threading.getContainer $routeParams.id
      $scope.focus $scope.thread.message.annotation
    else
      $scope.detail = false
      $scope.focus $scope.annotations

    if $routeParams.bucket?
      $scope.annotations = heatmap.buckets[$routeParams.bucket]
    else
      unless $scope.detail
        datum = (d3.select heatmap.element[0]).datum()
        if datum?
          {highlights, offset} = datum
          bottom = offset + heatmap.element.height()
          $scope.annotations = highlights.reduce (acc, hl) =>
            if hl.offset.top >= offset and hl.offset.top <= bottom
              if hl.data not in acc
                acc.push hl.data
            acc
          , []
        else
          $scope.annotations = []


angular.module('h.controllers', [])
  .controller('AppController', App)
  .controller('AnnotationController', Annotation)
  .controller('EditorController', Editor)
  .controller('ViewerController', Viewer)
