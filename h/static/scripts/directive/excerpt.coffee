###*
# @ngdoc directive
# @name excerpt
# @restrict C
# @description Checks to see if text is overflowing its container.
# If so, it prepends/appends expanders/collapsers.
###
module.exports = [ '$timeout', ($timeout) ->
  link: (scope, elem, attr, ctrl) ->
    # Check for excerpts when annotations are created.
    scope.$on 'annotationCreated', (event) ->
      scope.excerpt()

    # Check for excerpts when annotations are updated.
    scope.$on 'annotationUpdated', (event) ->
      scope.excerpt()

    # Check for excerpts on thread collapse toggle.
    scope.$on 'threadToggleCollapse', (value) ->
      scope.excerpt()

    do scope.excerpt = ->
      $timeout ->
        if elem.find('.more').length == 0
          if elem[0].scrollHeight > elem[0].clientHeight
            elem.prepend angular.element '<span class="more"> More...</span>'
            if elem.hasClass('annotation-quote')
              offset = 6
            else if elem.hasClass('annotation-body')
              offset = 9
            else offset = 0
            elem.find('.more').css({
                top: elem[0].clientHeight + offset
            })
            elem.append angular.element '<span class="less"> Less ^</span>'
            elem.find('.more').on 'click', ->
              $(this).hide()
              elem.addClass('show-full-excerpt')
            elem.find('.less').on 'click', ->
              elem.find('.more').show()
              elem.removeClass('show-full-excerpt')
  restrict: 'C'
]
