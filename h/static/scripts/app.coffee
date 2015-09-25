require('autofill-event')
baseURI = require('document-base-uri')
angular = require('angular')
require('angular-websocket')
require('angular-jwt')

uuid = require('node-uuid')
clientId = uuid.v4()

socket = null

resolve =
  store: ['store', (store) -> store.$promise]
  streamer: [
    '$websocket', 'annotationMapper'
    ($websocket,   annotationMapper) ->
      # Get the socket URL
      url = new URL('/ws', baseURI)
      url.protocol = url.protocol.replace('http', 'ws')

      # Close any existing socket
      socket?.close()

      # Open the socket
      socket = $websocket(url.href, [], {reconnectIfNotNormalClose: true})
      socket.send(messageType: 'client_id', value: clientId)

      # Listen for updates
      socket.onMessage (event) ->
        message = JSON.parse(event.data)
        return if !message or message.type != 'annotation-notification'
        action = message.options.action
        annotations = message.payload
        return unless annotations?.length
        switch action
          when 'create', 'update', 'past'
            annotationMapper.loadAnnotations annotations
          when 'delete'
            annotationMapper.unloadAnnotations annotations

      return socket
  ]
  threading: [
    'annotationMapper', 'drafts', 'threading'
    (annotationMapper,   drafts,   threading) ->
      # Unload all the annotations
      idTable = threading.idTable
      annotations = (message for id, {message} of idTable when message)
      annotationMapper.unloadAnnotations(annotations)

      # Reset the threading root
      threading.createIdTable([])
      threading.root = mail.messageContainer()

      # Thread all the drafts
      threading.thread(drafts.all())

      return threading
  ]


configureDocument = ['$provide', ($provide) ->
  $provide.decorator '$document', ($delegate) ->
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
  # Explicitly whitelist '.html' paths adjacent to application base URI
  # TODO: move all front-end templates into their own directory for safety
  basePattern = new URL('**.html', baseURI).href
  $sceDelegateProvider.resourceUrlWhitelist ['self', basePattern]
]


setupCrossFrame = ['crossframe', (crossframe) -> crossframe.connect()]

setupHttp = ['$http', ($http) ->
  $http.defaults.headers.common['X-Client-Id'] = clientId
]

setupHost = ['host', (host) -> ]

setupFeatures = ['features', (features) -> features.fetch()]

module.exports = angular.module('h', [
  'angulartics'
  'angulartics.google.analytics'
  'angular-jwt'
  'bootstrap'
  'ngAnimate'
  'ngResource'
  'ngRoute'
  'ngSanitize'
  'ngTagsInput'
  'ngWebSocket'
  'toastr'
  require('./vendor/ui-bootstrap-custom-0.13.4')
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
.directive('groupList', require('./directive/group-list').directive)
.directive('markdown', require('./directive/markdown'))
.directive('privacy', require('./directive/privacy').directive)
.directive('simpleSearch', require('./directive/simple-search'))
.directive('statusButton', require('./directive/status-button'))
.directive('thread', require('./directive/thread'))
.directive('threadFilter', require('./directive/thread-filter'))
.directive('match', require('./directive/match'))
.directive('spinner', require('./directive/spinner'))
.directive('tabbable', require('./directive/tabbable'))
.directive('tabReveal', require('./directive/tab-reveal'))
.directive('shareDialog', require('./directive/share-dialog'))
.directive('windowScroll', require('./directive/window-scroll'))
.directive('dropdownMenuBtn', require('./directive/dropdown-menu-btn'))
.directive('publishAnnotationBtn', require('./directive/publish-annotation-btn'))

.filter('converter', require('./filter/converter'))
.filter('moment', require('./filter/moment'))
.filter('persona', require('./filter/persona'))
.filter('urlencode', require('./filter/urlencode'))
.filter('documentTitle', require('./filter/document-title'))
.filter('documentDomain', require('./filter/document-domain'))

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
.service('pulse', require('./pulse'))
.service('queryParser', require('./query-parser'))
.service('render', require('./render'))
.service('searchFilter', require('./search-filter'))
.service('session', require('./session'))
.service('store', require('./store'))
.service('streamFilter', require('./stream-filter'))
.service('tags', require('./tags'))
.service('time', require('./time'))
.service('threading', require('./threading'))
.service('unicode', require('./unicode'))
.service('viewFilter', require('./view-filter'))

.factory('serviceUrl', require('./service-url'))

.value('AnnotationSync', require('./annotation-sync'))
.value('AnnotationUISync', require('./annotation-ui-sync'))
.value('Discovery', require('./discovery'))

.config(configureDocument)
.config(configureLocation)
.config(configureRoutes)
.config(configureTemplates)

.run(setupFeatures)
.run(setupCrossFrame)
.run(setupHttp)
.run(setupHost)
