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
    'annotator', 'queryparser', 'searchfilter', 'streamfilter'
  ]
  constructor: (
     $scope,   $rootScope,
     annotator,   queryparser,   searchfilter,   streamfilter
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

    annotator.plugins.Store?.annotations = []
    $rootScope.applyView 'Document'  # Non-sensical but works for now
    $rootScope.applySort 'Newest'


angular.module('h.streamsearch', imports, configure)
.controller('StreamSearchController', StreamSearch)
