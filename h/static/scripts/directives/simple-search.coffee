simpleSearch = ['$parse', ($parse) ->
  uuid = 0
  link: (scope, elem, attr, ctrl) ->
    _search = $parse(attr.onsearch)
    _clear = $parse(attr.onclear)

    scope.viewId = uuid++
    scope.dosearch = ->
      _search(scope, {"this": scope.searchtext})

    scope.reset = (event) ->
      event.preventDefault()
      scope.searchtext = ''
      _clear(scope) if attr.onclear

    scope.$watch attr.query, (query) ->
      if query?
        scope.searchtext = query
        _search(scope, {"this": scope.searchtext})

  restrict: 'C'
  template: '''
            <form class="simple-search-form" ng-class="!searchtext && 'simple-search-inactive'" name="searchBox" ng-submit="dosearch()">
              <input id="simple-search-{{viewId}}" class="simple-search-input" type="text" ng-model="searchtext" name="searchText" placeholder="Search…" />
              <label for="simple-search-{{viewId}}" class="simple-search-icon icon-search"></label>
              <button class="simple-search-clear" type="reset" ng-hide="!searchtext" ng-click="reset($event)">
                <i class="icon-x"></i>
              </button>
            </form>
            '''
]


angular.module('h.directives').directive('simpleSearch', simpleSearch)
