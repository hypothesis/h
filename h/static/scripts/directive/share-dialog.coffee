###*
# @ngdoc directive
# @name share-dialog
# @restrict A
# @description This dialog generates a via link to the page h is currently
# loaded on.
###
module.exports = ['crossframe', (crossframe) ->
  link: (scope, elem, attrs, ctrl) ->
    scope.viaPageLink = ''

    # Watch scope.shareDialog.visible: when it changes to true, focus input
    # and selection.
    scope.$watch (-> scope.shareDialog?.visible), (visible) ->
      if visible
        scope.$evalAsync(-> elem.find('#via').focus().select())

    scope.$watchCollection (-> crossframe.providers), ->
      if crossframe.providers?.length
        # XXX: Consider multiple providers in the future
        p = crossframe.providers[0]
        if p.entities?.length
          e = p.entities[0]
          scope.viaPageLink = 'https://via.hypothes.is/' + e

  restrict: 'A'
  templateUrl: 'share_dialog.html'
]
