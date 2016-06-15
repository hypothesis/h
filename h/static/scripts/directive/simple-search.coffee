module.exports = ->
  bindToController: true
  controllerAs: 'vm'
  controller: ['$element', '$http', '$scope', ($element, $http, $scope) ->
    self = this
    button = $element.find('button')
    input = $element.find('input')[0]
    form = $element.find('form')[0]

    button.on('click', -> input.focus())

    $scope.$watch (-> $http.pendingRequests.length), (pending) ->
      self.loading = (pending > 0)

    form.onsubmit = (e) ->
      e.preventDefault()
      self.onSearch({$query: input.value})

    this.inputClasses = ->
      'is-expanded': self.alwaysExpanded || self.query.length > 0

    this.$onChanges = (changes) ->
      if changes.query
        input.value = changes.query.currentValue

    self
  ]
  restrict: 'E'
  scope:
    # Specifies whether the search input field should always be expanded,
    # regardless of whether the it is focused or has an active query.
    #
    # If false, it is only expanded when focused or when 'query' is non-empty
    alwaysExpanded: '<'
    query: '<'
    onSearch: '&'
  template: '''
            <form class="simple-search-form"
                  name="searchForm"
                  ng-class="!vm.query && 'simple-search-inactive'">
              <input class="simple-search-input"
                     type="text"
                     name="query"
                     placeholder="{{vm.loading && 'Loading' || 'Search'}}…"
                     ng-disabled="vm.loading"
                     ng-class="vm.inputClasses()"/>
              <button type="button" class="simple-search-icon top-bar__btn" ng-hide="vm.loading">
                <i class="h-icon-search"></i>
              </button>
              <button type="button" class="simple-search-icon btn btn-clean" ng-show="vm.loading" disabled>
                <span class="btn-icon"><span class="spinner"></span></span>
              </button>
            </form>
            '''
