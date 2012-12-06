class App
  this.$inject = ['$compile', '$http', '$location', '$scope', 'annotator']
  constructor: ($compile, $http, $location, $scope, annotator) ->
    {plugins} = annotator

    $location.path '/app/viewer'

    $scope.$on 'reset', =>
      angular.extend $scope,
        personas: []
        persona: null
        token: null

    $scope.$watch 'personas', (newValue, oldValue) =>
      if newValue?.length
        annotator.element.find('#persona')
          .off('change').on('change', -> $(this).submit())
          .off('click')
        $scope.showAuth = false
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

    # Fetch the initial model from the server
    $http.get 'model',
      withCredentials: true
    .success (data) =>
      angular.extend $scope, data

    # Set the initial state
    # Asynchronous so that other controllers get time to initialize
    $scope.$evalAsync "$broadcast('reset')"


class Auth
  this.$inject = ['$compile', '$element', '$http', '$scope', 'deform']
  constructor: ($compile, $element, $http, $scope, deform) ->
    $scope.submit = ->
      controls = $element.find('.sheet .active form').formSerialize()
      $http.post '', controls,
        headers:
          'Content-Type': 'application/x-www-form-urlencoded'
        withCredentials: true
      .success (data) =>
        # Extend the scope with updated model data
        angular.extend($scope, data.model) if data.model?

        # Replace any forms which were re-rendered in this response
        for oid of data.form
          target = '#' + oid

          $form = $(data.form[oid])
          $form.replaceAll(target)

          link = $compile $form
          link $scope

          deform.focusFirstInput target

    $scope.$on 'reset', =>
      angular.extend $scope,
        auth: null
        username: null
        password: null
        email: null
        code: null

    $scope.$on 'showAuth', => $scope.auth = 'login'


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
  .controller('Auth', Auth)
  .controller('Viewer', Viewer)
