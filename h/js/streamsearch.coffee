get_quote = (annotation) ->
  if annotation.quote? then return annotation.quote
  if not 'target' in annotation then return ''

  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '
  quote

class StreamSearch
  this.inject = ['$element', '$location', '$scope', '$timeout', 'streamfilter']
  constructor: (
    $element, $location, $scope, $timeout, streamfilter
  ) ->
    $scope.path = window.location.protocol + '//' + window.location.hostname + ':' +
      window.location.port + '/__streamer__'

    # Generate client ID
    buffer = new Array(16)
    uuid.v4 null, buffer, 0
    @clientID = uuid.unparse buffer

    # Read search params
    search_query = ''
    params = $location.search()
    if params.query?
      search_query = params.query

    # Initialize Visual search
    @search = VS.init
      container: $element.find('.visual-search')
      query: search_query
      callbacks:
        search: (query, searchCollection) =>
          console.log 'search'

          # Do not search when no facet is given
          unless searchCollection.models.length > 0
            return

          # Past data limit
          limit = 100

          # First cluster the different facets into categories
          categories = {}
          for searchItem in searchCollection.models
            category = searchItem.attributes.category
            value = searchItem.attributes.value
            if category is 'limit' then limit = value
            else
              if category is 'text'
                # Visualsearch sickly automatically cluster the text field
                # (and only the text filed) into a space separated string
                catlist = []
                for val in value.split ' '
                  catlist.push val
                categories[category] = catlist
              else
                if category in categories then categories[category].push value
                else categories[category] = [value]

          # Assemble the filter json
          filter =
            streamfilter
              .setPastDataHits(limit)
              .setMatchPolicyIncludeAll()
              .noClauses()

          console.log categories

          for category, value of categories
            if value.length is 1
              filter.addClausesParse(category + ':i=' + value)
            else
              filter.addClausesParse(category + ':i[' + value)

          $scope.initStream filter.getFilter()

          # Update the parameters
          $location.search
            'query' : query

        facetMatches: (callback) =>
          return callback ['text','tag', 'quote','time','user', 'limit'], {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'limit' then callback [0, 10, 25, 100, 250, 1000]
            when 'time'
              callback ['5 min', '30 min', '1 hour', '12 hours', '1 day', '1 week', '1 month', '1 year'], {preserveOrder: true}
        clearSearch: (original) =>
          # Execute clearSearch's internal method for resetting search
          original()
          $scope.$apply -     >
            $scope.annotations = []
            $location.search {}

    $scope.initStream = (filter) ->
      if $scope.sock? then $scope.sock.close()
      $scope.annotations = new Array()
      $scope.sock = new SockJS($scope.path)

      $scope.sock.onopen = =>
        sockmsg =
          filter: filter
          clientID: @clientID
        $scope.sock.send JSON.stringify sockmsg

      $scope.sock.onclose = =>
        # stream is closed

      $scope.sock.onmessage = (msg) =>
        console.log 'Got something'
        console.log msg
        unless msg.data.type? and msg.data.type is 'annotation-notification'
          return
        data = msg.data.payload
        action = msg.data.options.action
        unless data instanceof Array then data = [data]

        $scope.$apply =>
          $scope.manage_new_data data, action

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        annotation._share_link = window.location.protocol +
        '//' + window.location.hostname + ':' + window.location.port + "/a/" + annotation.id
        annotation._anim = 'fade'

        switch action
          when 'create', 'past'
            unless annotation in $scope.annotations
              $scope.annotations.unshift annotation
          when 'update'
            index = 0
            for ann in $scope.annotations
              if ann.id is annotation.id
                # Remove the original
                $scope.annotations.splice index,1
                # Put back the edited
                $scope.annotations.unshift annotation
                break
              index +=1
          when 'delete'
            for ann in $scope.annotations
              if ann.id is annotation.id
                $scope.annotations.splice index,1
                break
              index +=1

    $scope.annotations = []
    if search_query.length > 0
      $timeout =>
        @search.searchBox.app.options.callbacks.search @search.searchBox.value(), @search.searchBox.app.searchQuery
      ,500

angular.module('h.streamsearch',['h.streamfilter','h.filters','h.directives','bootstrap'])
  .controller('StreamSearchController', StreamSearch)
