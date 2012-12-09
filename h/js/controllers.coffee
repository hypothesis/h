class App
  this.$inject = [
    '$compile', '$element', '$http', '$location', '$scope',
    'annotator', 'deform'
  ]
  constructor: (
    $compile, $element, $http, $location, $scope,
    annotator, deform
  ) ->
    {plugins, provider} = annotator
    heatmap = annotator.plugins.Heatmap
    heatmap.element.appendTo $element

    # Thread the annotations after loading
    annotator.subscribe 'annotationsLoaded', (annotations) =>
      $scope.$apply =>
        $scope.threads = mail.messageThread().thread annotations.map (a) =>
          m = mail.message(null, a.id, a.thread?.split('/') or [])
          m.annotation = a
          m

    # Update the heatmap when certain events are pubished
    events = [
      'annotationCreated'
      'annotationDeleted'
      'annotationsLoaded'
      'hostUpdated'
    ]

    for event in events
      annotator.subscribe event, =>
        provider.getHighlights ({highlights, offset}) =>
          heatmap.updateHeatmap
            highlights: highlights.map (hl) =>
              hl.data = annotator.cache[hl.data]
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
          unless $location.path() == '/viewer' and $location.search()?.detail?
            provider.setActiveHighlights heatmap.buckets[bucket]?.map (a) =>
              a.hash.valueOf()

        # Gets rid of them after
        .on 'mouseout', =>
          if $location.path() == '/viewer'
            unless $location.search()?.detail?
              bucket = heatmap.buckets[$location.search()?.bucket]
              provider.setActiveHighlights bucket?.map (a) =>
                a.hash.valueOf()
          else
            provider.setActiveHighlights null

        # Does one of a few things when a tab is clicked depending on type
        .on 'mouseup', (bucket) =>
          d3.event.preventDefault()

          # If it's the upper tab, scroll to next bucket above
          if heatmap.isUpper bucket
            threshold = offset + heatmap.index[0]
            next = highlights.reduce (next, hl) ->
              if next < hl.offset.top < threshold then hl.offset.top else next
            , threshold - height
            provider.scrollTop next - pad
            $location.search('bucket').replace()

          # If it's the lower tab, scroll to next bucket below
          else if heatmap.isLower bucket
            threshold = offset + heatmap.index[0] + pad
            next = highlights.reduce (next, hl) ->
              if threshold < hl.offset.top < next then hl.offset.top else next
            , offset + height
            provider.scrollTop next - pad
            $location.search('bucket').replace()

          # If it's neither of the above, load the bucket into the viewer
          else
            $scope.$apply =>
              $location
                .path('/viewer')
                .search
                  bucket: bucket
                  detail: null
                .replace()
            annotator.show()

    angular.extend $scope,
      auth: null
      forms: []

    $scope.reset = ->
      angular.extend $scope,
        auth: null
        username: null
        password: null
        email: null
        code: null
        personas: []
        persona: null
        token: null

    $scope.addForm = ($form, name) ->
      $scope.forms[name] = $form

    $scope.submit = ->
      fields = switch $scope.auth
        when 'login' then ['username', 'password']
        when 'register' then ['username', 'password', 'email']
        when 'forgot' then ['email']
        when 'activate' then ['password', 'code']
      params = ([key, $scope[key]] for key in fields when $scope[key]?)
      params.push ['__formid__', $scope.auth]
      data = (((p.map encodeURIComponent).join '=') for p in params).join '&'

      $http.post '', data,
        headers:
          'Content-Type': 'application/x-www-form-urlencoded'
        withCredentials: true
      .success (data) =>
        # Extend the scope with updated model data
        angular.extend($scope, data.model) if data.model?

        # Compile and link any forms which were re-rendered in this response
        for oid of data.form
          $form = angular.element data.form[oid]
          if oid of $scope.forms
            $scope.forms[oid].replaceWith $form
          ($compile $form) $scope
          deform.focusFirstInput $form

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
        $scope.auth = null
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

    $scope.$on 'showAuth', (event, show=true) =>
      $scope.auth = if show then 'login' else null

    # Fetch the initial model from the server
    $scope.reset()
    $http.get 'model',
      withCredentials: true
    .success (data) =>
      angular.extend $scope, data


class Editor
  this.$inject = ['$routeParams', '$scope', 'annotator']
  constructor: ($routeParams, $scope, annotator) ->
    angular.extend $scope,
      annotation: annotator.cache[$routeParams.hash.valueOf()]
      editable: true
    this


class Viewer
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator'
  ]
  constructor: (
    $location, $routeParams, $scope,
    annotator
  ) ->
    $scope.annotation = null
    $scope.annotations = []

    $scope.showDetail = (annotation) ->
      $location.search
        bucket: null
        detail: annotation.id

    $scope.$on '$routeChangeSuccess', =>
      update = => $scope.$emit '$routeUpdate'
      annotator.plugins.Heatmap.subscribe 'updated', update
      $scope.$on '$routeChangeStart', =>
        annotator.plugins.Heatmap.unsubscribe 'updated', update
      update()

    $scope.$on '$routeUpdate', =>
      this.refresh $scope, $routeParams, annotator

    this

  refresh: ($scope, $routeParams, annotator) =>
    if $routeParams.bucket?
      buckets = annotator.plugins.Heatmap.buckets
      $scope.annotations = buckets[$routeParams.bucket]
    else
      if not $routeParams.detail?
        heatmap = annotator.plugins.Heatmap
        datum = (d3.select heatmap.element[0]).datum()
        if datum
          {highlights, offset} = d3.select(heatmap.element[0]).datum()
          bottom = offset + heatmap.element.height()
          $scope.annotations = highlights.reduce (acc, hl) =>
            if hl.offset.top >= offset and hl.offset.top <= bottom
              if hl.data not in acc
                acc.push hl.data
            acc
          , []
        else
          $scope.annotations = []

    if $routeParams.detail?
      thread = $scope.threads.getSpecificChild $routeParams.detail
      $scope.detail = true
      $scope.annotation = thread?.message.annotation
      annotator.provider.setActiveHighlights [$scope.annotation.hash.valueOf()]
    else
      $scope.detail = false
      annotator.provider.setActiveHighlights $scope.annotations?.map (a) =>
        a.hash.valueOf()


angular.module('h.controllers', [])
  .controller('App', App)
  .controller('Editor', Editor)
  .controller('Viewer', Viewer)
