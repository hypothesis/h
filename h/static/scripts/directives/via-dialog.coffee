###*
# @ngdoc directive
# @name viaLinkDialog
# @restrict A
# @description The dialog that generates a via link to the page h is currently
# loaded on.
###
viaLinkDialog = ['$timeout', ($timeout) ->
    link: (scope, elem, attrs, ctrl) ->
        ## Watch vialinkvisble: when it changes to true, focus input and selection.
        scope.$watch (-> scope.viaLinkVisible), (visble) ->
            if visble
                $timeout (-> elem.find('#via').focus().select()), 0, false
                
    controller: ($scope, $element, $attrs) ->
    	$scope.viaLinkVisible = false
    	$scope.viaPageLink = 'https://via.hypothes.is/h/' + document.referrer
    templateUrl: 'via_dialog.html'
]

###*
# @ngdoc directive
# @name shareThisPage
# @restrict A
# @description Link to show the via dialog.
###
shareThisPage = ->
    require: '?^viaLink'		
    template: '<a href="" ng-click="viaLinkVisible = true">Share this page</a>'

angular.module('h')
.directive('shareThisPage', shareThisPage)
.directive('viaLinkDialog', viaLinkDialog)
