###*
# @ngdoc service
# @name pulse
# @param {Element} elem Element to pulse.
# @description
# Pulses an element to indicate activity in that element.
###
module.exports = ['$animate', ($animate) ->
  (elem) ->
    $animate.addClass elem, 'pulse', ->
      $animate.removeClass(elem, 'pulse')
]
