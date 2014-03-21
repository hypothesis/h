imports = [
  'bootstrap'
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
  '$locationProvider', '$provide', '$routeProvider', '$sceDelegateProvider',
  (
   $locationProvider,   $provide,   $routeProvider,   $sceDelegateProvider
  ) ->
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

    if window.location.href.match /^chrome-extension:\/\//
      # XXX: This hack is awful. It shouldn't be necessary.
      # Angular should have the default 'self' work on extension pages.
      $sceDelegateProvider.resourceUrlWhitelist [
        'self'
        '.*'
      ]
]


angular.module('h', imports, configure)
