imports = [
  'bootstrap'
  'ngRoute'
  'h.controllers'
  'h.directives'
  'h.app_directives'
  'h.displayer'
  'h.flash'
  'h.filters'
  'h.services'
]


configure = [
  '$locationProvider', '$routeProvider', '$sceDelegateProvider',
  (
   $locationProvider,   $routeProvider,   $sceDelegateProvider,
  ) ->
    $locationProvider.html5Mode(true)

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

    if window.location.href.match /^chrome-extension:\/\//
      # XXX: This hack is awful. It shouldn't be necessary.
      # Angular should have the default 'self' work on extension pages.
      $sceDelegateProvider.resourceUrlWhitelist [
        'self'
        '.*'
      ]
]


angular.module('h', imports, configure)
