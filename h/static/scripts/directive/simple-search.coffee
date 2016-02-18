module.exports = ['$http', '$parse', ($http, $parse) ->
  link: (scope, elem, attr, ctrl) ->
    button = elem.find('button')
    input = elem.find('input')

    button.on('click', -> input[0].focus())

    scope.reset = (event) ->
      event.preventDefault()
      scope.query = ''
      scope.searchtext = ''

    scope.search = (event) ->
      event.preventDefault()
      scope.query = scope.searchtext

    scope.$watch (-> $http.pendingRequests.length), (pending) ->
      scope.loading = (pending > 0)

    scope.$watch 'query', (query) ->
      return if query is undefined
      scope.searchtext = query
      if query
        scope.onSearch?(query: scope.searchtext)
      else
        scope.onClear?()

  restrict: 'E'
  scope:
    # Specifies whether the search input field should always be expanded,
    # regardless of whether the it is focused or has an active query.
    #
    # If false, it is only expanded when focused or when 'query' is non-empty
    alwaysExpanded: '<'
    query: '='
    onSearch: '&'
    onClear: '&'
  template: '''
            <form class="simple-search-form" ng-class="!searchtext && 'simple-search-inactive'" name="searchBox" ng-submit="search($event)">
              <input class="simple-search-input" type="text" ng-model="searchtext" name="searchText"
                     placeholder="{{loading && 'Loading' || 'Search'}}…"
                     ng-disabled="loading"
                     ng-class="(alwaysExpanded || searchtext.length > 0) ? 'is-expanded' : ''"/>
              <button type="button" class="simple-search-icon top-bar__btn" ng-hide="loading">
                <i class="h-icon-search"></i>
              </button>
              <button type="button" class="simple-search-icon btn btn-clean" ng-show="loading" disabled>
                <span class="btn-icon"><span class="spinner"></span></span>
              </button>
            </form>
            '''
]
