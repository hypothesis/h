imports = [
  'bootstrap'
  'h.controllers'
  'h.directives'
  'h.filters'
  'h.flash'
  'h.searchfilters'
]

class StreamSearch
  this.inject = [
    '$scope', '$rootScope',
    'queryparser', 'searchfilter', 'streamfilter'
  ]
  constructor: (
     $scope,   $rootScope,
     queryparser,   searchfilter,   streamfilter
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()
      .setPastDataHits(50)

    # Apply query clauses
    terms = searchfilter.generateFacetedFilter $scope.search.query
    queryparser.populateFilter streamfilter, terms

    $scope.updater?.then (sock) ->
      filter = streamfilter.getFilter()
      sock.send(JSON.stringify({filter}))

    $rootScope.annotations = []
    $rootScope.applyView "Document"  # Non-sensical, but best for the moment
    $rootScope.applySort "Newest"

    $scope.openDetails = (annotation) ->

    $scope.loadMore = (number) ->
      unless $scope.updater? then return
      sockmsg =
        messageType: 'more_hits'
        moreHits: number

      $scope.updater.then (sock) ->
        sock.send(JSON.stringify(sockmsg))


angular.module('h.streamsearch', imports, configure)
.controller('StreamSearchController', StreamSearch)
