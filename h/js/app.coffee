imports = [
  'bootstrap'
  'h.controllers'
  'h.directives'
  'h.displayer'
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
  $routeProvider.otherwise
    redirectTo: '/viewer'
configure.$inject = ['$routeProvider']


angular.module('h', imports, configure)
