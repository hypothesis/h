class App
  this.$inject = [
    '$compile', '$http', '$location', '$scope',
    'annotator', 'deform'
  ]
  constructor: ($compile, $http, $location, $scope, annotator, deform) ->
    {plugins} = annotator

    angular.extend $scope,
      auth: null
      forms: []

    $scope.reset = =>
      angular.extend $scope,
        auth: null
        username: null
        password: null
        email: null
        code: null
        personas: []
        persona: null
        token: null

    $scope.addForm = ($form, name) =>
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
        plugins.Auth.withToken plugins.Permissions._setAuthFromToken
      else
        plugins.Permissions.setUser(null)
        delete plugins.Auth

    $scope.$on 'showAuth', (event, show=true) =>
      $scope.auth = if show then 'login' else null

    # Fetch the initial model from the server
    $scope.reset()
    $http.get 'model',
      withCredentials: true
    .success (data) =>
      angular.extend $scope, data
      $location.path '/app/viewer'


class Viewer
  this.$inject = ['$location', '$routeParams', '$scope', 'annotator']
  constructor: ($location, $routeParams, $scope, annotator) ->
    thread = null

    annotator.subscribe 'annotationsLoaded', (annotations) =>
      thread = mail.messageThread().thread annotations.map (a) =>
        m = mail.message(null, a.id, a.thread?.split('/') or [])
        m.annotation = a
        m

      # TODO: deal with empty parents
      $scope.$apply (scope) =>
        scope.annotations = (t.message.annotation for t in thread.children)

    $scope.annotation = null
    $scope.annotations = []

    $scope.getThread = (id) =>
      if thread? then (thread.getSpecificChild id) else null

    $scope.showDetail = (annotation) =>
      $location.search 'detail', annotation.id

    $scope.$on '$routeUpdate', =>
      if $routeParams.detail?
        thread = thread?.getSpecificChild $routeParams.detail
        $scope.annotation = thread?.message.annotation
      else
        $scope.annotation = null


angular.module('h.controllers', [])
  .controller('App', App)
  .controller('Viewer', Viewer)
