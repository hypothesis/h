angular = require('angular')
mail = require('./vendor/jwz')


module.exports = class StreamController
  this.inject = [
    '$scope', '$rootScope', '$routeParams',
    'auth', 'queryParser', 'searchFilter', 'store',
    'streamer', 'streamFilter', 'annotationMapper'
  ]
  constructor: (
     $scope,   $rootScope,   $routeParams
     auth,   queryParser,   searchFilter,   store,
     streamer,   streamFilter, annotationMapper
  ) ->
    # Initialize cards
    $scope.threadRoot = mail.messageContainer()

    $rootScope.$on 'beforeAnnotationCreated', (event, annotation) ->
      container = mail.messageContainer(annotation)
      $scope.threadRoot.addChild container

    $rootScope.$on 'annotationCreated', (event, annotation) ->
      for child in ($scope.threadRoot.children or []) \
      when child.message is annotation
        child.message = null
        $scope.threadRoot.removeChild child
        container = mail.messageContainer(annotation)
        $scope.threadRoot.addChild container
        break

    $rootScope.$on 'annotationDeleted', (event, annotation) ->
      for child in ($scope.threadRoot.children or []) \
      when child.message is annotation
        child.message = null
        $scope.threadRoot.removeChild child
        break

    $rootScope.$on 'annotationsLoaded', (event, annotations) ->
      for annotation in annotations
        container = mail.messageContainer(annotation)
        $scope.threadRoot.addChild container

    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchFilter.generateFacetedFilter $scope.search.query
    queryParser.populateFilter streamFilter, terms
    streamer.send({filter: streamFilter.getFilter()})

    # Perform the search
    searchParams = searchFilter.toObject $scope.search.query
    query = angular.extend limit: 10, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''
