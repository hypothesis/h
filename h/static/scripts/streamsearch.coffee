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

class StreamSearch
  this.inject = [
    '$location', '$scope', '$rootScope',
    'queryparser', 'session', 'searchfilter', 'streamfilter'
  ]
  constructor: (
     $location,   $scope,   $rootScope,
     queryparser,   session,   searchfilter,   streamfilter
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()
      .setPastDataHits(50)

    # Apply query clauses
    $scope.query = $location.search()['query']
    terms = searchfilter.generateFacetedFilter $scope.query
    queryparser.populateFilter streamfilter, terms

    $scope.updater?.then (sock) ->
      filter = streamfilter.getFilter()
      sock.send(JSON.stringify({filter}))

    $rootScope.annotations = []
    $rootScope.applyView "Document"  # Non-sensical, but best for the moment
    $rootScope.applySort "Newest"

    $scope.search.query = $location.search()
    $scope.search.show = not angular.equals($location.search(), {})

    $scope.search.update = (query) ->
      unless angular.equals $location.search(query), query
        $location.search {query:query}

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
.controller('StreamSearchController', StreamSearch)
