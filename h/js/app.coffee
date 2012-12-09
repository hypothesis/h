imports = [
  'bootstrap'
  'deform'
  'h.controllers'
  'h.directives'
  'h.filters'
  'h.services'
]


configure = ($routeProvider) ->
  $routeProvider.when '/editor',
    controller: 'Editor'
    templateUrl: 'editor.html'
  $routeProvider.when '/viewer',
    controller: 'Viewer'
    reloadOnSearch: false
    templateUrl: 'viewer.html'
configure.$inject = ['$routeProvider']


angular.module('h', imports, configure)
