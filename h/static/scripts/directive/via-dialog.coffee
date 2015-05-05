###*
# @ngdoc directive
# @name viaLinkDialog
# @restrict A
# @description The dialog that generates a via link to the page h is currently
# loaded on.
###
module.exports = ['$timeout', 'crossframe', ($timeout, crossframe) ->
    viaUrl = 'https://via.hypothes.is/h/'
    link: (scope, elem, attrs, ctrl) ->
        scope.viaPageLink = ''

        ## Watch viaLinkVisible: when it changes to true, focus input and selection.
        scope.$watch (-> scope.viaLinkVisible), (visible) ->
            if visible
                $timeout (-> elem.find('#via').focus().select()), 0, false

        scope.$watchCollection (-> crossframe.providers), ->
            if crossframe.providers?.length
                # XXX: Consider multiple providers in the future
                p = crossframe.providers[0]
                if p.entities?.length
                    e = p.entities[0]
                    scope.viaPageLink = viaUrl + e
    controller: 'AppController'
    templateUrl: 'via_dialog.html'
]
