imports = [
  'bootstrap'
  'h.directives'
  'h.filters'
  'h.helpers'
  'h.streamfilter'
]


get_quote = (annotation) ->
  if annotation.quote? then return annotation.quote
  if not 'target' in annotation then return ''

  quote = '(Reply annotation)'
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector'
            quote = selector['exact'] + ' '
  quote

# This class will process the results of search and generate the correct filter
# It expects the following dict format as rules
# { facet_name : {
#      formatter: to format the value (optional)
#      path: json path mapping to the annotation field
#      exact_match: true|false (default: true)
#      case_sensitive: true|false (default: false)
#      and_or: and|or for multiple values should it threat them as 'or' or 'and' (def: or)
#      es_query_string: should the streaming backend use query_string es query for this facet
#      operator: if given it'll use this operator regardless of other circumstances
# }
# The models is the direct output from visualsearch
# The limit is the default limit
class SearchHelper
  populateFilter: (filter, models, rules, limit = 50) ->
    # First cluster the different facets into categories
    categories = {}
    for searchItem in models
      category = searchItem.attributes.category
      value = searchItem.attributes.value

      if category is 'results' then limit = value
      else
        if category is 'text'
          # Visualsearch sickly automatically cluster the text field
          # (and only the text filed) into a space separated string
          catlist = []
          catlist.push val for val in value.split ' '
          categories[category] = catlist
        else
          if category of categories then categories[category].push value
          else categories[category] = [value]

    filter.setPastDataHits(limit)

    # Now for the categories
    for category, values of categories
      unless rules[category]? then continue
      unless values.length then continue
      rule = rules[category]

      # Now generate the clause with the help of the rule
      exact_match = if rule.exact_match? then rule.exact_match else true
      case_sensitive = if rule.case_sensitive? then rule.case_sensitive else false
      and_or = if rule.and_or? then rule.and_or else 'or'
      mapped_field = if rule.path? then rule.path else '/'+category
      es_query_string = if rule.es_query_string? then rule.es_query_string else false

      if values.length is 1
        oper_part =
          if rule.operator? then rule.operator
          else if exact_match then 'equals' else 'matches'
        value_part = if rule.formatter then rule.formatter values[0] else values[0]
        filter.addClause mapped_field, oper_part, value_part, case_sensitive, es_query_string
      else
        if and_or is 'or'
          val_list = ''
          first = true
          for val in values
            unless first then val_list += ',' else first = false
            value_part = if rule.formatter then rule.formatter val else val
            val_list += value_part
          oper_part =
            if rule.operator? then rule.operator
            else if exact_match then 'one_of' else 'match_of'
          filter.addClause mapped_field, oper_part, val_list, case_sensitive, es_query_string
        else
          oper_part =
            if rule.operator? then rule.operator
            else if exact_match then 'equals' else 'matches'
          for val in values
            value_part = if rule.formatter then rule.formatter val else val
            filter.addClause mapped_field, oper_part, value_part, case_sensitive, es_query_string

    if limit != 50 then categories['results'] = [limit]
    [filter.getFilter(), categories]

class StreamSearch
  facets: ['text','tags', 'uri', 'quote','since','user','results']
  rules:
    user:
      formatter: (user) ->
        'acct:' + user + '@' + window.location.hostname
      path: '/user'
      exact_match: true
      case_sensitive: false
      and_or: 'or'
    text:
      path: '/text'
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    tags:
      path: '/tags'
      exact_match: false
      case_sensitive: false
      and_or: 'or'
    quote:
      path: "/quote"
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    uri:
      formatter: (uri) ->
        uri = uri.toLowerCase()
        if uri.match(/http:\/\//) then uri = uri.substring(7)
        if uri.match(/https:\/\//) then uri = uri.substring(8)
        if uri.match(/^www\./) then uri = uri.substring(4)
        uri
      path: '/uri'
      exact_match: false
      case_sensitive: false
      es_query_string: true
      and_or: 'or'
    since:
      formatter: (past) ->
        seconds =
          switch past
            when '5 min' then 5*60
            when '30 min' then 30*60
            when '1 hour' then 60*60
            when '12 hours' then 12*60*60
            when '1 day' then 24*60*60
            when '1 week' then 7*24*60*60
            when '1 month' then 30*24*60*60
            when '1 year' then 365*24*60*60
        new Date(new Date().valueOf() - seconds*1000)
      path: '/created'
      exact_match: false
      case_sensitive: true
      and_or: 'and'
      operator: 'ge'

  this.inject = ['$element', '$location', '$scope', '$timeout', 'baseURI','streamfilter']
  constructor: (
    $element, $location, $scope, $timeout, baseURI, streamfilter
  ) ->
    prefix = baseURI.replace /\/\w+(\/?\??[^\/]*)\/?$/, ''
    $scope.empty = false

    # Generate client ID
    buffer = new Array(16)
    uuid.v4 null, buffer, 0
    @clientID = uuid.unparse buffer

    $scope.sortAnnotations = (a, b) ->
      a_upd = if a.updated? then new Date(a.updated) else new Date()
      b_upd = if b.updated? then new Date(b.updated) else new Date()
      a_upd.getTime() - b_upd.getTime()

    # Read search params
    search_query = ''
    params = $location.search()
    for param, values of params
      # Ignore non facet parameters
      if param in @facets
        unless values instanceof Array then values = [values]
        for value in values
          search_query += param + ': "' + value + '" '

    # Initialize Visual search
    @search = VS.init
      container: $element.find('.visual-search')
      query: search_query
      callbacks:
        search: (query, searchCollection) =>
          # Assemble the filter json
          filter =
            streamfilter
              .setMatchPolicyIncludeAll()
              .noClauses()

          [filter, $scope.categories] =
            new SearchHelper().populateFilter filter, searchCollection.models, @rules
          $scope.initStream filter

          # Update the parameters
          $location.search $scope.categories

        facetMatches: (callback) =>
          # Created and limit should be singleton.
          add_limit = true
          add_created = true
          for facet in @search.searchQuery.facets()
            if facet.hasOwnProperty 'results' then add_limit = false
            if facet.hasOwnProperty 'since' then add_created = false

          if add_limit and add_created then list = ['text','tags', 'uri', 'quote','since','user','results']
          else
            if add_limit then list = ['text','tags', 'uri', 'quote','user', 'results']
            else
              if add_created then list = ['text','tags', 'uri', 'quote','since','user']
              else list = ['text','tags', 'uri', 'quote','user']

          return callback list, {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'results'
              callback ['0', '10', '25', '50', '100', '250', '1000']
            when 'since'
              callback ['5 min', '30 min', '1 hour', '12 hours', '1 day', '1 week', '1 month', '1 year'], {preserveOrder: true}
        clearSearch: (original) =>
          # Execute clearSearch's internal method for resetting search
          original()
          $scope.$apply ->
            $scope.annotations = []
            $scope.empty = false
            $location.search {}

    $scope.initStream = (filter) ->
      if $scope.sock? then $scope.sock.close()
      $scope.annotations = new Array()

      $scope.sock = new SockJS prefix + '/__streamer__'

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

        if data.length
          $scope.$apply =>
            $scope.empty = false
            $scope.manage_new_data data, action
        else
          unless $scope.annotations.length
            $scope.$apply =>
              $scope.empty = true

    $scope.manage_new_data = (data, action) =>
      for annotation in data
        annotation.action = action
        annotation.quote = get_quote annotation
        annotation._share_link = prefix + '/a/' + annotation.id

        if annotation in $scope.annotations then continue

        switch action
          when 'create', 'past'
            unless annotation in $scope.annotations
              $scope.annotations.unshift annotation
          when 'update'
            index = 0
            found = false
            for ann in $scope.annotations
              if ann.id is annotation.id
                # Remove the original
                $scope.annotations.splice index,1
                # Put back the edited
                $scope.annotations.unshift annotation
                found = true
                break
              index +=1
            # Sometimes editing an annotation makes it appear in the list
            # If it wasn't part of it before. (i.e. adding a new tag)
            unless found
              $scope.annotations.unshift annotation
          when 'delete'
            index = 0
            for ann in $scope.annotations
              if ann.id is annotation.id
                $scope.annotations.splice index,1
                break
              index +=1

      $scope.annotations = $scope.annotations.sort($scope.sortAnnotations).reverse()

    $scope.loadMore = (number) =>
      console.log 'loadMore'
      unless $scope.sock? then return
      sockmsg =
        messageType: 'more_hits'
        clientID: @clientID
        moreHits: number

      $scope.sock.send JSON.stringify sockmsg


    $scope.annotations = []
    $timeout =>
      @search.searchBox.app.options.callbacks.search @search.searchBox.value(), @search.searchBox.app.searchQuery
    ,500


configure = [
  '$locationProvider'
  ($locationProvider) ->
    $locationProvider.html5Mode(true)
]


angular.module('h.streamsearch', imports, configure)
.controller('StreamSearchController', StreamSearch)
