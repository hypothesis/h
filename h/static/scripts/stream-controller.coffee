angular = require('angular')
mail = require('./vendor/jwz')


module.exports = class StreamController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'queryParser', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'threading', 'annotationMapper'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     queryParser,   searchFilter,   store,
     streamer,   streamFilter,   threading,   annotationMapper
  ) ->
    # XXX: disable page search
    $scope.search = {}

    # XXX: Reset the threading service
    threading.idTable = threading.createIdTable([])
    $scope.threadRoot = threading.root = mail.messageContainer()

    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    terms = searchFilter.generateFacetedFilter $routeParams.q
    queryParser.populateFilter streamFilter, terms
    streamer.send({filter: streamFilter.getFilter()})

    # Perform the search
    searchParams = searchFilter.toObject $routeParams.q
    query = angular.extend limit: 20, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true
