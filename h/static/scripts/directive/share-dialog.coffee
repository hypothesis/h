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

    scope.$watchCollection (-> crossframe.frames), (frames) ->
      if not frames.length
        return
      # XXX: Consider sharing multiple frames in the future?
      scope.viaPageLink = 'https://via.hypothes.is/' + frames[0].uri

  restrict: 'A'
  templateUrl: 'share_dialog.html'
]
