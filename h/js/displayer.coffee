angular.module('h.displayer',[])
  .controller('DisplayerCtrl',
  ($scope, $element) ->
    $scope.toggleCollapse = (event, replynumber, thread) ->
      #Plus/minus sign and italics
      elem = (angular.element event.srcElement).parent()
      if elem.hasClass 'hyp-collapsed'
        elem.removeClass 'hyp-collapsed'
        expand = true
      else elem.addClass 'hyp-collapsed'

      #Now for the replies
      if replynumber
        toggle_elem = $element.find('.thread_' + (thread+1)).parent().parent()
        if expand? then toggle_elem.removeAttr 'style'
        else toggle_elem.css 'display', 'none'
)