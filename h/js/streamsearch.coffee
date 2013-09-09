class StreamSearch
  this.inject = ['$element','$scope']
  constructor: (
    $element, $scope
  ) ->
    search_query = ''
    @search = VS.init
      container: $element.find('.visual-search')
      query: search_query
      callbacks:
        search: (query, searchCollection) =>
          console.log 'search'
        facetMatches: (callback) =>
          return callback ['text','tag', 'quote', 'scope', 'group','time','user'], {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'group' then callback ['Public', 'Private']
            when 'scope' then callback ['sidebar', 'document']
            when 'time'
              callback ['5 min', '30 min', '1 hour', '12 hours', '1 day', '1 week', '1 month', '1 year'], {preserveOrder: true}


angular.module('h.streamsearch',['bootstrap'])
  .controller('StreamSearchController', StreamSearch)
