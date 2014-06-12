imports = [
  'bootstrap'
  'h.controllers'
  'h.directives'
  'h.filters'
  'h.flash'
  'h.helpers'
  'h.session'
  'h.socket'
  'h.streamfilter'
]

SEARCH_FACETS = ['text', 'tags', 'uri', 'quote', 'since', 'user', 'results']
SEARCH_VALUES =
  group: ['Public', 'Private'],
  since: ['5 min', '30 min', '1 hour', '12 hours',
          '1 day', '1 week', '1 month', '1 year']

class StreamSearch
  this.inject = [
    '$location', '$rootScope', '$scope', '$timeout',
    'annotator', 'baseURI', 'queryparser', 'session', 'socket', 'streamfilter'
  ]
  constructor: (
     $location, $rootScope, $scope, $timeout,
     annotator, baseURI, queryparser, session, socket, streamfilter
  ) ->
    $scope.empty = false

    $scope.removeAnnotations = ->
      $rootScope.annotations = []
      if annotator.plugins.Store?
        # Copy annotation list
        annotations = annotator.plugins.Store.annotations.splice(0)
        # XXX: Temporary workaround until client-side delete only is implemented
        annotator.plugins.Store.annotations = []
        annotator.deleteAnnotation annotation for annotation in annotations

        annotations = []

    $scope.search.update = (searchCollection) ->
      return unless searchCollection.models.length

      # Empty the stream
      $scope.removeAnnotations()

      # Assemble the filter json
      filter =
        streamfilter
          .resetFilter()
          .setMatchPolicyIncludeAll()
          .setPastDataHits(50)

      query = queryparser.populateFilter filter, searchCollection.models
      filter = streamfilter.getFilter()

      session.$promise.then ->
        $scope.updater.then (sock) ->
          sock.send(JSON.stringify(filter: filter))

      # Update the parameters
      $location.search query

    $scope.search.clear = ->
      $scope.removeAnnotations()
      filter =
        streamfilter
          .resetFilter()
          .setPastDataHits(50)
      $location.search({})

    $scope.openDetails = (annotation) ->
    $scope.loadMore = (number) =>
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.send(JSON.stringify(sockmsg))

    $scope.search.query = -> $scope.query
    $scope.query = $location.search()

    $scope.$on 'RefreshSearch', ->
      $rootScope.$broadcast 'VSSearch'

    $rootScope.$broadcast 'VSSearch'
angular.module('h.streamsearch', imports, configure)
.constant('searchFacets', SEARCH_FACETS)
.constant('searchValues', SEARCH_VALUES)
.controller('StreamSearchController', StreamSearch)
