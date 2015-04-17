angular = require('angular')
mail = require('./vendor/jwz')

module.exports = class StreamController
# To survive reloads
  threadRoot: mail.messageContainer()
  idTable: {}

  this.inject = [
    '$rootScope', '$routeParams', '$scope',
    'annotationMapper', 'drafts', 'queryParser', 'searchFilter', 'store',
    'streamer', 'streamFilter',
  ]
  constructor: (
     $rootScope,   $routeParams,   $scope,
     annotationMapper,   drafts,   queryParser,   searchFilter,   store,
     streamer,   streamFilter,
  ) ->
    # Initialize streamer cards
    $scope.threadRoot = @threadRoot

    # Initialize the base filter
    streamFilter
      .resetFilter()
      .setMatchPolicyIncludeAll()

    # Apply query clauses
    $scope.search.query = $routeParams.q
    terms = searchFilter.generateFacetedFilter $scope.search.query
    queryParser.populateFilter streamFilter, terms
    streamer.send({filter: streamFilter.getFilter()})

    # Listen to updates
    streamer.onmessage = (data) =>
      return if !data or data.type != 'annotation-notification'
      action = data.options.action
      payload = data.payload

      return unless payload.length
      switch action
        when 'create', 'update', 'past'
          annotationMapper.loadAnnotations payload
        when 'delete'
          for annotation in payload
            if a = @idTable[annotation.id]?.message
              $scope.$emit('annotationDeleted', a)

      $scope.$digest()

    # Perform the search
    searchParams = searchFilter.toObject $scope.search.query
    query = angular.extend limit: 20, searchParams
    store.SearchResource.get query, ({rows}) ->
      annotationMapper.loadAnnotations(rows)

    $scope.isEmbedded = false
    $scope.isStream = true

    $scope.sort.name = 'Newest'

    $scope.shouldShowThread = (container) -> true

    $scope.$on '$destroy', ->
      $scope.search.query = ''

    beforeAnnotationCreated =  (event, annotation) =>
      container = mail.messageContainer(annotation)
      $scope.threadRoot.addChild container
      if annotation.id?
        @idTable[annotation.id] = container


    annotationCreated = (event, annotation) =>
      for child in ($scope.threadRoot.children or []) \
      when child.message is annotation
        if child.message.id?
          delete @idTable[child.id]

        child.message = null
        $scope.threadRoot.removeChild child

        container = mail.messageContainer(annotation)
        $scope.threadRoot.addChild container
        if annotation.id?
          @idTable[annotation.id] = container
        break

    annotationDeleted = (event, annotation) =>
      for child in ($scope.threadRoot.children or []) \
      when child.message is annotation
        child.message = null
        $scope.threadRoot.removeChild child
        if annotation.id?
          delete @idTable[annotation.id]
        break

    annotationsLoaded = (event, annotations) =>
      for annotation in annotations
        if @idTable[annotation.id]?.message
          @idTable[annotation.id].message = annotation
        else
          container = mail.messageContainer(annotation)
          $scope.threadRoot.addChild container
          @idTable[annotation.id] = container

    cleanupAnnotations = =>
      # Clean up any annotations that need to be unloaded.
      for id, container of @idTable when container.message
        $scope.$emit('annotationDeleted', container.message)
        drafts.remove container.message

    listeners = [
      $rootScope.$on('beforeAnnotationCreated', beforeAnnotationCreated)
      $rootScope.$on('annotationCreated', annotationCreated)
      $rootScope.$on('annotationDeleted', annotationDeleted)
      $rootScope.$on('annotationsLoaded', annotationsLoaded)
      $rootScope.$on('cleanupAnnotations', cleanupAnnotations)
    ]

    $scope.$on '$destroy', ->
      unbind() for unbind in listeners
