class StreamSearchController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'auth', 'queryparser', 'searchfilter', 'store',
    'streamer', 'streamfilter', 'annotationMapper'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     auth,   queryparser,   searchfilter,   store,
     streamer,   streamfilter, annotationMapper
  ) ->
    # Initialize the base filter
    streamfilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchfilter.generateFacetedFilter $scope.search.query
    queryparser.populateFilter streamfilter, terms
    streamer.send({filter: streamfilter.getFilter()})

    # Perform the search
    searchParams = searchfilter.toObject $scope.search.query
    query = angular.extend limit: 10, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

      # Fetch parents
      ancestors = []
      for annotation in rows
        if annotation.references?
          for id in annotation.references
            ancestors.push(id) if id not in ancestors

      for id in ancestors
        store.AnnotationResource.read {id: id}, (annotation) ->
          annotationMapper.loadAnnotations([annotation])

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) ->
      container.message isnt null

    $scope.$on '$destroy', ->
      $scope.search.query = ''

angular.module('h')
.controller('StreamSearchController', StreamSearchController)
