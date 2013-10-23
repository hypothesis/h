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


configure = ($routeProvider) ->
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
configure.$inject = ['$routeProvider']


angular.module('h', imports, configure)
