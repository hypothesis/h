###*
# @ngdoc directive
# @name viaLinkDialog
# @restrict A
# @description The dialog that generates a via link to the page h is currently
# loaded on.
###
viaLinkDialog = ['$timeout', '$document', ($timeout, $document) ->
    link: (scope, elem, attrs, ctrl) ->
        ## Watch vialinkvisble: when it changes to true, focus input and selection.
        scope.$watch (-> scope.viaLinkVisible), (visble) ->
            if visble
                $timeout (-> elem.find('#via').focus().select()), 0, false
        
        scope.viaPageLink = 'https://via.hypothes.is/h/' + $document[0].referrer
    controller: 'AppController'
    templateUrl: 'via_dialog.html'
]

angular.module('h')
.directive('viaLinkDialog', viaLinkDialog)
