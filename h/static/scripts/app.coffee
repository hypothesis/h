Annotator = require('annotator')
angular = require('angular')
uuid = require('node-uuid')

resolve =
  auth: ['$q', '$rootScope', 'auth', ($q, $rootScope, auth) ->
    dfd = $q.defer()
    unwatch = $rootScope.$watch (-> auth.user), (user) ->
      return if user is undefined
      dfd.resolve(auth)
      unwatch()
    dfd.promise
  ]
  store: ['store', (store) -> store.$promise]


configureDocument = ['$provide', ($provide) ->
  $provide.decorator '$document', ($delegate) ->
    baseURI = $delegate.prop('baseURI')
    baseURI ?= $delegate.find('base').prop('href')  # fallback
    baseURI ?= $delegate.prop('URL')                # fallback
    $delegate.prop('baseURI', baseURI)
]


configureLocation = ['$locationProvider', ($locationProvider) ->
  # Use HTML5 history
  $locationProvider.html5Mode(true)
]


configureRoutes = ['$routeProvider', ($routeProvider) ->
  $routeProvider.when '/a/:id',
    controller: 'AnnotationViewerController'
    templateUrl: 'viewer.html'
    reloadOnSearch: false
    resolve: resolve
  $routeProvider.when '/viewer',
    controller: 'WidgetController'
    templateUrl: 'viewer.html'
    reloadOnSearch: false
    resolve: resolve
  $routeProvider.when '/stream',
    controller: 'StreamController'
    templateUrl: 'viewer.html'
    reloadOnSearch: false
    resolve: resolve
  $routeProvider.otherwise
    redirectTo: '/viewer'
]


configureTemplates = ['$sceDelegateProvider', ($sceDelegateProvider) ->
  # Configure CSP for templates
  # XXX: IE workaround for the lack of document.baseURI property
  baseURI = document.baseURI
  if not baseURI
    baseTags = document.getElementsByTagName "base"
    baseURI = if baseTags.length then baseTags[0].href else document.URL

  # Explicitly whitelist '.html' paths adjacent to application base URI
  # TODO: move all front-end templates into their own directory for safety
  basePattern = baseURI.replace /\/[^\/]*$/, '/**.html'
  $sceDelegateProvider.resourceUrlWhitelist ['self', basePattern]
]


setupCrossFrame = ['crossframe', (crossframe) -> crossframe.connect()]

setupHost = ['host', (host) -> ]

setupStreamer = [
  '$http', '$window', 'streamer'
  ($http,   $window,   streamer) ->
    clientId = uuid.v4()
    streamer.clientId = clientId
    $.ajaxSetup(headers: {'X-Client-Id': clientId})
    $http.defaults.headers.common['X-Client-Id'] = clientId
]

module.exports = angular.module('h', [
  'angulartics'
  'angulartics.google.analytics'
  'bootstrap'
  'ngAnimate'
  'ngResource'
  'ngRoute'
  'ngSanitize'
  'ngTagsInput'
  'toastr'
])

.controller('AppController', require('./app-controller'))
.controller('AnnotationUIController', require('./annotation-ui-controller'))
.controller('AnnotationViewerController', require('./annotation-viewer-controller'))
.controller('StreamController', require('./stream-controller'))
.controller('WidgetController', require('./widget-controller'))

.directive('annotation', require('./directive/annotation'))
.directive('deepCount', require('./directive/deep-count'))
.directive('formInput', require('./directive/form-input'))
.directive('formValidate', require('./directive/form-validate'))
.directive('markdown', require('./directive/markdown'))
.directive('privacy', require('./directive/privacy'))
.directive('simpleSearch', require('./directive/simple-search'))
.directive('statusButton', require('./directive/status-button'))
.directive('thread', require('./directive/thread'))
.directive('threadFilter', require('./directive/thread-filter'))
.directive('whenscrolled', require('./directive/whenscrolled'))
.directive('match', require('./directive/match'))
.directive('spinner', require('./directive/spinner'))
.directive('tabbable', require('./directive/tabbable'))
.directive('tabReveal', require('./directive/tab-reveal'))
.directive('shareDialog', require('./directive/share-dialog'))

.filter('converter', require('./filter/converter'))
.filter('moment', require('./filter/moment'))
.filter('persona', require('./filter/persona'))
.filter('urlencode', require('./filter/urlencode'))

.provider('identity', require('./identity'))
.provider('session', require('./session'))

.service('annotator', -> new Annotator(angular.element('<div>')))
.service('annotationMapper', require('./annotation-mapper'))
.service('annotationUI', require('./annotation-ui'))
.service('auth', require('./auth'))
.service('bridge', require('./bridge'))
.service('crossframe', require('./cross-frame'))
.service('drafts', require('./drafts'))
.service('flash', require('./flash'))
.service('formRespond', require('./form-respond'))
.service('host', require('./host'))
.service('localStorage', require('./local-storage'))
.service('permissions', require('./permissions'))
.service('pulse', require('./pulse'))
.service('queryParser', require('./query-parser'))
.service('render', require('./render'))
.service('searchFilter', require('./search-filter'))
.service('store', require('./store'))
.service('streamFilter', require('./stream-filter'))
.service('streamer', require('./streamer'))
.service('tags', require('./tags'))
.service('time', require('./time'))
.service('threading', require('./threading'))
.service('unicode', require('./unicode'))
.service('viewFilter', require('./view-filter'))

.value('AnnotationSync', require('./annotation-sync'))
.value('AnnotationUISync', require('./annotation-ui-sync'))
.value('Discovery', require('./discovery'))

.config(configureDocument)
.config(configureLocation)
.config(configureRoutes)
.config(configureTemplates)

.run(setupCrossFrame)
.run(setupStreamer)
.run(setupHost)
