simpleSearch = ['$parse', ($parse) ->
  uuid = 0
  link: (scope, elem, attr, ctrl) ->
    scope.viewId = uuid++

    scope.reset = (event) ->
      event.preventDefault()
      scope.query = ''

    scope.search = (event) ->
      event.preventDefault()
      scope.query = scope.searchtext

    scope.$watch 'query', (query) ->
      return if query is undefined
      scope.searchtext = query
      if query
        scope.onSearch?(query: scope.searchtext)
      else
        scope.onClear?()

  restrict: 'C'
  scope:
    query: '='
    onSearch: '&'
    onClear: '&'
  template: '''
            <form class="simple-search-form" ng-class="!searchtext && 'simple-search-inactive'" name="searchBox" ng-submit="search($event)">
              <input id="simple-search-{{viewId}}" class="simple-search-input" type="text" ng-model="searchtext" name="searchText" placeholder="Search…" />
              <label for="simple-search-{{viewId}}" class="simple-search-icon h-icon-search"></label>
              <button class="simple-search-clear" type="reset" ng-hide="!searchtext" ng-click="reset($event)">
                <i class="h-icon-x"></i>
              </button>
            </form>
            '''
]


angular.module('h')
.directive('simpleSearch', simpleSearch)
