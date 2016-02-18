# initialize Raven. This is required at the top of this file
# so that it happens early in the app's startup flow
settings = require('./settings')(document)
if settings.raven
  require('./raven').init(settings.raven)


require('autofill-event')
angular = require('angular')
require('angular-jwt')

streamer = require('./streamer')

resolve =
  # Ensure that we have available a) the current authenticated userid, and b)
  # the list of user groups.
  sessionState: ['session', (session) -> session.load()]
  store: ['store', (store) -> store.$promise]
  streamer: streamer.connect
  threading: [
    'annotationMapper', 'drafts', 'threading'
    (annotationMapper,   drafts,   threading) ->
      # Unload all the annotations
      annotationMapper.unloadAnnotations(threading.annotationList())

      # Reset the threading root
      threading.createIdTable([])
      threading.root = mail.messageContainer()

      # Reload all new, unsaved annotations
      threading.thread(drafts.unsaved())

      return threading
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

setupCrossFrame = ['crossframe', (crossframe) -> crossframe.connect()]

setupHttp = ['$http', ($http) ->
  $http.defaults.headers.common['X-Client-Id'] = streamer.clientId
]

setupHost = ['host', (host) -> ]

module.exports = angular.module('h', [
  require('./raven').angularModule().name
  'angulartics'
  'angulartics.google.analytics'
  'angular-jwt'
  'ngAnimate'
  'ngResource'
  'ngRoute'
  'ngSanitize'
  'ngTagsInput'
  'toastr'
  'ui.bootstrap'
])

.controller('AppController', require('./app-controller'))
.controller('AnnotationUIController', require('./annotation-ui-controller'))
.controller('AnnotationViewerController', require('./annotation-viewer-controller'))
.controller('StreamController', require('./stream-controller'))
.controller('WidgetController', require('./widget-controller'))

.directive('annotation', require('./directive/annotation').directive)
.directive('deepCount', require('./directive/deep-count'))
.directive('excerpt', require('./directive/excerpt').directive)
.directive('formInput', require('./directive/form-input'))
.directive('formValidate', require('./directive/form-validate'))
.directive('groupList', require('./directive/group-list').directive)
.directive('hAutofocus', require('./directive/h-autofocus'))
.directive('loginForm', require('./directive/login-form').directive)
.directive('markdown', require('./directive/markdown'))
.directive('simpleSearch', require('./directive/simple-search'))
.directive('statusButton', require('./directive/status-button'))
.directive('thread', require('./directive/thread'))
.directive('threadFilter', require('./directive/thread-filter'))
.directive('spinner', require('./directive/spinner'))
.directive('shareDialog', require('./directive/share-dialog'))
.directive('windowScroll', require('./directive/window-scroll'))
.directive('dropdownMenuBtn', require('./directive/dropdown-menu-btn'))
.directive('publishAnnotationBtn', require('./directive/publish-annotation-btn'))
.directive('searchStatusBar', require('./directive/search-status-bar'))
.directive('sidebarTutorial', require('./directive/sidebar-tutorial').directive)
.directive('signinControl', require('./directive/signin-control'))
.directive('sortDropdown', require('./directive/sort-dropdown'))
.directive('topBar', require('./directive/top-bar'))

.filter('converter', require('./filter/converter'))

.provider('identity', require('./identity'))

.service('annotationMapper', require('./annotation-mapper'))
.service('annotationUI', require('./annotation-ui'))
.service('auth', require('./auth'))
.service('bridge', require('./bridge'))
.service('crossframe', require('./cross-frame'))
.service('drafts', require('./drafts'))
.service('features', require('./features'))
.service('flash', require('./flash'))
.service('formRespond', require('./form-respond'))
.service('groups', require('./groups'))
.service('host', require('./host'))
.service('localStorage', require('./local-storage'))
.service('permissions', require('./permissions'))
.service('queryParser', require('./query-parser'))
.service('render', require('./render'))
.service('searchFilter', require('./search-filter'))
.service('session', require('./session'))
.service('streamFilter', require('./stream-filter'))
.service('tags', require('./tags'))
.service('time', require('./time'))
.service('threading', require('./threading'))
.service('unicode', require('./unicode'))
.service('viewFilter', require('./view-filter'))

.factory('store', require('./store'))

.value('AnnotationSync', require('./annotation-sync'))
.value('AnnotationUISync', require('./annotation-ui-sync'))
.value('Discovery', require('./discovery'))
.value('raven', require('./raven'))
.value('settings', settings)

.config(configureLocation)
.config(configureRoutes)

.run(setupCrossFrame)
.run(setupHttp)
.run(setupHost)
