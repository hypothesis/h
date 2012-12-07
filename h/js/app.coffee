imports = [
    'bootstrap'
    'deform'
    'h.controllers'
    'h.directives'
    'h.filters'
    'h.services'
]


configure = ($routeProvider) ->
  $routeProvider.when '/viewer',
    controller: 'Viewer'
    reloadOnSearch: false
    templateUrl: 'viewer.html'
configure.$inject = ['$routeProvider']


angular.module('h', imports, configure)
