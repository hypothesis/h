module.exports = ['$location', '$anchorScroll', ($location, $anchorScroll) ->
  return (
    restrict: 'A'
    link: (scope, element, attrs) ->
      $location.hash(attrs.scrolltome)
      $anchorScroll()
  )
]
