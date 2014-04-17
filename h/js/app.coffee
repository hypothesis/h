imports = [
  'bootstrap'
  'ngAnimate'
  'ngRoute'
  'h.controllers'
  'h.directives'
  'h.app_directives'
  'h.displayer'
  'h.helpers'
  'h.flash'
  'h.filters'
  'h.services'
]


configure = [
  '$httpProvider', '$locationProvider', '$provide', '$routeProvider',
  '$sceDelegateProvider',
  (
   $httpProvider,   $locationProvider,   $provide,   $routeProvider,
   $sceDelegateProvider,
  ) ->
    # Use the Pyramid XSRF header name
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'

    $locationProvider.html5Mode(true)

    # Disable annotating while drafting
    $provide.decorator 'drafts', [
      'annotator', '$delegate',
      (annotator,   $delegate) ->
        {add, remove} = $delegate

        $delegate.add = (draft) ->
          add.call $delegate, draft
          annotator.disableAnnotating $delegate.isEmpty()

        $delegate.remove = (draft) ->
          remove.call $delegate, draft
          annotator.enableAnnotating $delegate.isEmpty()

        $delegate
      ]

    $routeProvider.when '/editor',
      controller: 'EditorController'
      templateUrl: 'editor.html'
    $routeProvider.when '/viewer',
      controller: 'ViewerController'
      reloadOnSearch: false
      templateUrl: 'viewer.html'
    $routeProvider.when '/page_search',
      controller: 'SearchController'
      reloadOnSearch: false
      templateUrl: 'page_search.html'
    $routeProvider.otherwise
      redirectTo: '/viewer'

    # Configure CSP for templates
    # Explicitly whitelist '.html' paths adjacent to application base URI
    basePattern = document.baseURI.replace /\/[^\/]*$/, '/*.html'
    $sceDelegateProvider.resourceUrlWhitelist ['self', basePattern]
]


angular.module('h', imports, configure)
