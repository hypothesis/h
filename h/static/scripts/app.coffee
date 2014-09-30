imports = [
  'ngAnimate'
  'ngRoute'
  'ngSanitize'
  'ngTagsInput'
  'bootstrap'
  'h.auth'
  'h.helpers'
  'h.identity'
]


configure = [
  '$locationProvider', '$routeProvider', '$sceDelegateProvider',
  ($locationProvider,   $routeProvider,   $sceDelegateProvider) ->
    $locationProvider.html5Mode(true)

    $routeProvider.when '/a/:id',
      controller: 'AnnotationViewerController'
      templateUrl: 'viewer.html'
    $routeProvider.when '/viewer',
      controller: 'ViewerController'
      templateUrl: 'viewer.html'
      reloadOnSearch: false
    $routeProvider.when '/stream',
      controller: 'StreamSearchController'
      templateUrl: 'viewer.html'
    $routeProvider.otherwise
      redirectTo: '/viewer'

    # Configure CSP for templates
    # XXX: IE workaround for the lack of document.baseURI property
    baseURI = document.baseURI
    if not baseURI
      baseTags = document.getElementsByTagName "base"
      baseURI = if baseTags.length then baseTags[0].href else document.URL

    # Explicitly whitelist '.html' paths adjacent to application base URI
    # TODO: move all front-end templates into their own directory for safety
    basePattern = baseURI.replace /\/[^\/]*$/, '/**.html'
    $sceDelegateProvider.resourceUrlWhitelist ['self', basePattern]
]


angular.module('h', imports, configure)
