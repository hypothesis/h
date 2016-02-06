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

    viaInput = elem[0].querySelector('.js-via')

    # Watch scope.shareDialog.visible: when it changes to true, focus input
    # and selection.
    scope.$watch (-> scope.shareDialog?.visible), (visible) ->
      if visible
        scope.$evalAsync(->
          viaInput.focus()
          viaInput.select()
        )

    scope.$watchCollection (-> crossframe.frames), (frames) ->
      if not frames.length
        return
      # Check to see if we are on a via page. If so, we just return the URI.
      re = /https:\/\/via\.hypothes\.is/
      if re.test(frames[0].uri)
        scope.viaPageLink = frames[0].uri
      else
        scope.viaPageLink = 'https://via.hypothes.is/' + frames[0].uri

  restrict: 'E'
  templateUrl: 'share_dialog.html'
]
