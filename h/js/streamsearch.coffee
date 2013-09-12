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
#      exact_match: true|false (default: true)
#      case_sensitive: true|false (default: false)
#      and_or: and|or for multiple values should it threat them as 'or' or 'and' (def: or)
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
      if category is 'limit' then limit = value
      else
        if category is 'text'
          # Visualsearch sickly automatically cluster the text field
          # (and only the text filed) into a space separated string
          catlist = []
          catlist.push val for val in value.split ' '
          categories[category] = catlist
        else
          if category in categories then categories[category].push value
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

      if values.length is 1
        oper_part =
          if rule.operator? then rule.operator
          else if exact_match then 'equals' else 'matches'
        value_part = if rule.formatter then rule.formatter values[0] else values[0]
        filter.addClause '/'+category, oper_part, value_part, case_sensitive
      else
        if and_or is 'or'
          val_list = ''
          first = true
          for val in values
            unless first then val_list += ',' else first = false
            value_part = if rule.formatter then rule.formatter val else val
            value_list += value_part
          oper_part =
            if rule.operator? then rule.operator
            else if exact_match then 'one_of' else 'match_of'
          filter.addClause '/'+category, oper_part, value_part, case_sensitive
        else
          oper_part =
            if rule.operator? then rule.operator
            else if exact_match then 'equals' else 'matches'
          for val in values
            value_part = if rule.formatter then rule.formatter val else val
            filter.addClause '/'+category, oper_part, value_part, case_sensitive

    filter.getFilter()

class StreamSearch
  rules:
    user:
      formatter: (user) ->
        'acct:' + user + '@' + window.location.hostname
      exact_match: true
      case_sensitive: false
      and_or: 'or'
    text:
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    tags:
      exact_match: false
      case_sensitive: false
      and_or: 'or'
    quote:
      exact_match: false
      case_sensitive: false
      and_or: 'and'
    uri:
      formatter: (uri) ->
        uri = uri.toLowerCase()
        if url.match(/http:\/\//) then url = url.substring(7)
        if url.match(/https:\/\//) then url = url.substring(8)
        if url.match(/^www\./) then url = url.substring(4)
        uri
      exact_match: false
      case_sensitive: false
      and_or: 'or'
    created:
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
      exact_match: false
      case_sensitive: true
      and_or: 'and'
      operator: 'ge'

  this.inject = ['$element', '$location', '$scope', '$timeout', 'streamfilter']
  constructor: (
    $element, $location, $scope, $timeout, streamfilter
  ) ->
    $scope.path = window.location.protocol + '//' + window.location.hostname + ':' +
      window.location.port + '/__streamer__'
    $scope.empty = false

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
          # Assemble the filter json
          filter =
            streamfilter
              .setMatchPolicyIncludeAll()
              .noClauses()

          filter = new SearchHelper().populateFilter filter, searchCollection.models, @rules
          $scope.initStream filter

          # Update the parameters
          $location.search
            'query' : query

        facetMatches: (callback) =>
          # Created and limit should be singleton.
          add_limit = true
          add_created = true
          for facet in @search.searchQuery.facets()
            if facet.hasOwnProperty 'limit' then add_limit = false
            if facet.hasOwnProperty 'created' then add_created = false

          if add_limit and add_created then list = ['text','tags', 'uri', 'quote','created','user','limit']
          else
            if add_limit then list = ['text','tags', 'uri', 'quote','user', 'limit']
            else
              if add_created then list = ['text','tags', 'uri', 'quote','created','user']
              else list = ['text','tags', 'uri', 'quote','user']

          return callback list, {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'limit'
              callback ['0', '10', '25', '50', '100', '250', '1000']
            when 'created'
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
    $timeout =>
      @search.searchBox.app.options.callbacks.search @search.searchBox.value(), @search.searchBox.app.searchQuery
    ,500

angular.module('h.streamsearch',['h.streamfilter','h.filters','h.directives','bootstrap'])
  .controller('StreamSearchController', StreamSearch)
