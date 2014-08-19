class Viewer
  this.$inject = ['$location']
  constructor:   ( $location ) ->
    if $location.search()['q']
      return $location.path('/search').replace()

angular.module('h.widget.viewer', [])
.controller('ViewerController', Viewer)
