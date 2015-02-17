###*
# @ngdoc type
# @name threadList.ThreadListController
#
# @description
# `ThreadListController` wraps a list of {@link thread.ThreadController
# ThreadControllers}.
###
ThreadListController = [
  '$scope',
  ($scope) ->
    @container = $scope.getContainer()

    this
]

###*
# @ngdoc directive
# @name thread-list
###
threadList = ->
  controller: 'ThreadListController'
  controllerAs: 'vm'
  scope:
    getContainer: '&threadList'
    collapsed: '=threadListCollapsed'
    embedded: '=threadListEmbedded'
    orderBy: '=threadListOrderBy'
    focus: '&threadListFocus'
    hasFocus: '&threadListHasFocus'
    scrollTo: '&threadListScrollTo'
    shouldShow: '&threadListShouldShow'
  templateUrl: 'thread-list.html'

angular.module('h')
.controller('ThreadListController', ThreadListController)
.directive('threadList', threadList)
