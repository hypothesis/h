simpleSearch = ['$parse', ($parse) ->
  uuid = 0
  link: (scope, elem, attr, ctrl) ->
    scope.viewId = uuid++

    scope.reset = (event) ->
      event.preventDefault()
      scope.query = ''
      scope.onClear?()

    scope.search = (event) ->
      event.preventDefault()
      scope.query = scope.searchtext

    scope.$watch 'query', (query, old) ->
      return if query is old
      scope.searchtext = query
      if query
        scope.onSearch?(query: scope.searchtext)

  restrict: 'C'
  scope:
    query: '='
    onSearch: '&'
    onClear: '&'
  template: '''
            <form class="simple-search-form" ng-class="!searchtext && 'simple-search-inactive'" name="searchBox" ng-submit="search($event)">
              <input id="simple-search-{{viewId}}" class="simple-search-input" type="text" ng-model="searchtext" name="searchText" placeholder="Search…" />
              <label for="simple-search-{{viewId}}" class="simple-search-icon icon-search"></label>
              <button class="simple-search-clear" type="reset" ng-hide="!searchtext" ng-click="reset($event)">
                <i class="icon-x"></i>
              </button>
            </form>
            '''
]


angular.module('h.directives').directive('simpleSearch', simpleSearch)
