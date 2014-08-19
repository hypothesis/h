imports = [
  'ngRoute'
  'h.auth'
  'h.controllers'
  'h.directives'
  'h.services'
  'h.widget.head'
  'h.widget.editor'
  'h.widget.viewer'
  'h.widget.search'
]

configure = [
  '$locationProvider', '$provide', '$routeProvider', 'headProvider'
  ($locationProvider,   $provide,   $routeProvider,   headProvider) ->
    $locationProvider.html5Mode(true)

    # Disable annotating while drafting
    $provide.decorator 'drafts', [
      'annotator', '$delegate',
      (annotator,   $delegate) ->
        {add, remove} = $delegate

        $delegate.add = (draft) ->
          add.call $delegate, draft
          annotator.disableAnnotating $delegate.isEmpty()

        $delegate.remove = (draft) ->
          remove.call $delegate, draft
          annotator.enableAnnotating $delegate.isEmpty()

        $delegate
      ]

    # Export routes
    $routeProvider.when '/annotator.html',
      resolve:
        head: [
          '$location', '$window', 'head'
          ($location,   $window,  head) ->
            $location.path('/view')
            head
        ]
    $routeProvider.when '/edit',
      controller: 'EditorController'
      templateUrl: 'editor.html'
    $routeProvider.when '/view',
      controller: 'ViewerController'
      templateUrl: 'viewer.html'
    $routeProvider.when '/search',
      controller: 'SearchController'
      templateUrl: 'page_search.html'

    # Properties shared with other frames
    headProvider.whitelist = [
      'diffHTML', 'diffCaseOnly',
      'document', 'inject', 'quote', 'ranges', 'references', 'target', 'uri',
    ]
]


angular.module('h.widget', imports, configure)
