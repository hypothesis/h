imports = [
  'bootstrap'
  'h.controllers'
  'h.directives'
  'h.filters'
  'h.flash'
  'h.helpers'
  'h.session'
  'h.searchfilters'
]

SEARCH_FACETS = ['text', 'tags', 'uri', 'quote', 'since', 'user', 'results']
SEARCH_VALUES =
  group: ['Public', 'Private'],
  since: ['5 min', '30 min', '1 hour', '12 hours',
          '1 day', '1 week', '1 month', '1 year']

class StreamSearch
  this.inject = [
    '$location', '$scope', '$rootScope',
    'queryparser', 'session', 'streamfilter'
  ]
  constructor: (
     $location,   $scope,   $rootScope,
     queryparser,   session,   streamfilter
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()
      .setPastDataHits(50)

    # Apply query clauses
    queryparser.populateFilter streamfilter, $location.search()

    $scope.updater?.then (sock) ->
      filter = streamfilter.getFilter()
      sock.send(JSON.stringify({filter}))

    $rootScope.annotations = []
    $rootScope.applyView "Document"  # Non-sensical, but best for the moment
    $rootScope.applySort "Newest"

    $scope.search.query = $location.search()
    $scope.search.show = not angular.equals($location.search(), {})

    $scope.search.update = (searchCollection) ->
      # Update the query parameters
      query = queryparser.parseModels searchCollection.models
      unless angular.equals $location.search(), query
        $location.search query

    $scope.search.clear = ->
      $location.search({})

    $scope.openDetails = (annotation) ->
    $scope.loadMore = (number) =>
      # TODO: debounce
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.then (sock) ->
        sock.send(JSON.stringify(sockmsg))


angular.module('h.streamsearch', imports, configure)
.constant('searchFacets', SEARCH_FACETS)
.constant('searchValues', SEARCH_VALUES)
.controller('StreamSearchController', StreamSearch)
