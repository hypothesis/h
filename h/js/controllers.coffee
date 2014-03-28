class App
  scope:
    frame:
      visible: false
    sheet:
      collapsed: true
      tab: null
    ongoingHighlightSwitch: false

  this.$inject = [
    '$element', '$filter', '$http', '$location', '$rootScope', '$scope', '$timeout',
    'annotator', 'authentication', 'baseURI', 'streamfilter', 'viewFilter'
  ]
  constructor: (
    $element, $filter, $http, $location, $rootScope, $scope, $timeout
    annotator, authentication, baseURI, streamfilter, viewFilter
  ) ->
    {plugins, host, providers} = annotator
    
    #This must be set so the view sort controller can autohide. 
    $scope.show_search = false

    $scope.$watch 'auth.personas', (newValue, oldValue) =>
      unless newValue?.length
        authentication.persona = null
        authentication.token = null

        # Leave Highlighting mode when logging out
        if annotator.tool is 'highlight'
          # Because of logging out, we must leave Highlighting Mode.
          annotator.setTool 'comment'
          # No need to reload annotations after login, since the Social View
          # change (caused by leaving Highlighting Mode) will trigger
          # a reload anyway.
          $scope.skipAuthChangeReload = true

    $scope.$watch 'auth.persona', (newValue, oldValue) =>
      if oldValue? and not newValue?
        if annotator.discardDrafts()
          # TODO: better knowledge of routes
          authentication.$logout => $scope.$broadcast '$reset'
          $rootScope.applyView "Screen"
        else
          $scope.auth.persona = oldValue
      else if newValue?
        $scope.sheet.collapsed = true
        $rootScope.applyView "Screen"

    $scope.$watch 'auth.token', (newValue, oldValue) =>
      if plugins.Auth?
        plugins.Auth.token = newValue
        plugins.Auth.updateHeaders()

      if newValue?
        if not plugins.Auth?
          annotator.addPlugin 'Auth',
            tokenUrl: $scope.tokenUrl
            token: newValue
        else
          plugins.Auth.setToken(newValue)
        plugins.Auth.withToken (token) =>
          plugins.Permissions._setAuthFromToken token

          if annotator.ongoing_edit
            $timeout ->
              annotator.clickAdder()
            , 1000

          if $scope.ongoingHighlightSwitch
            $scope.ongoingHighlightSwitch = false
            annotator.setTool 'highlight'
      else
        plugins.Permissions.setUser(null)
        delete plugins.Auth

      if newValue isnt oldValue
        unless $scope.skipAuthChangeReload
          $scope.reloadAnnotations()
          if $scope.inSearch
            $timeout ->
              $rootScope.$broadcast 'ReRenderPageSearch'
            , 3000
        delete $scope.skipAuthChangeReload

    $scope.$watch 'socialView.name', (newValue, oldValue) ->
      return if newValue is oldValue
      console.log "Social View changed to '" + newValue + "'. Reloading annotations."
      $scope.reloadAnnotations()

    $scope.$watch 'frame.visible', (newValue, oldValue) ->
      routeName = $location.path().replace /^\//, ''
      if newValue
        annotator.show()
        annotator.host.notify method: 'showFrame', params: routeName
      else if oldValue
        $scope.sheet.collapsed = true
        annotator.hide()
        annotator.host.notify method: 'hideFrame', params: routeName
        for p in annotator.providers
          p.channel.notify method: 'setActiveHighlights'

    $scope.$watch 'sheet.collapsed', (hidden) ->
      unless hidden then $scope.sheet.tab = 'login'

    $scope.$watch 'sheet.tab', (tab) ->
      return unless tab

      $timeout =>
        $element
        .find('form')
        .filter(-> this.name is tab)
        .find('input')
        .filter(-> this.type isnt 'hidden')
        .first()
        .focus()
      , 10

      reset = $timeout (-> $scope.$broadcast '$reset'), 60000
      unwatch = $scope.$watch 'sheet.tab', (newTab) ->
        $timeout.cancel reset
        if newTab
          reset = $timeout (-> $scope.$broadcast '$reset'), 60000
        else
          $scope.ongoingHighlightSwitch = false
          delete annotator.ongoing_edit
          unwatch()

    $scope.$on 'back', ->
      return unless annotator.discardDrafts()
      if $location.path() == '/viewer' and $location.search()?.id?
        $location.search('id', null).replace()
      else
        annotator.hide()

    $scope.$on 'showAuth', (event, show=true) ->
      angular.extend $scope.sheet,
        collapsed: !show
        tab: 'login'

    $scope.$on '$reset', =>
      delete annotator.ongoing_edit
      base = angular.copy @scope
      angular.extend $scope, base,
        auth: authentication
        frame: $scope.frame or @scope.frame
        socialView: annotator.socialView

    $scope.$on 'success', (event, action) ->
      if action == 'claim'
        $scope.sheet.tab = 'activate'

    $scope.$broadcast '$reset'

    $rootScope.view = 'Screen'

    # Clean up the searchbar
    $scope.leaveSearch = =>
      # Got back from search page
      $scope.show_search = false

      # We have to call all these internal methods
      # of VS, because the public API does not have
      # a method for clearing search.
      @visualSearch.searchBox.disableFacets();
      @visualSearch.searchBox.value('');
      @visualSearch.searchBox.flags.allSelected = false;
      # Set host/guests into dynamic bucket mode
      for p in annotator.providers
        p.channel.notify
          method: 'setDynamicBucketMode'
          params: true

    $scope.$on '$routeChangeStart', (current, next) ->
      return unless next.$$route?

      # Will we be in search mode after this change?
      willSearch = next.$$route?.controller is "SearchController"

      if $scope.inSearch and not willSearch
        # We were in search mode, but we are leaving it now.
        $scope.leaveSearch()

      $scope.inSearch = willSearch

    # Update scope with auto-filled form field values
    $timeout ->
      for i in $element.find('input') when i.value
        $i = angular.element(i)
        $i.triggerHandler('change')
        $i.triggerHandler('input')
    , 200  # We hope this is long enough

    search_query = ''

    @visualSearch = VS.init
      container: $element.find('.visual-search')
      query: search_query
      callbacks:
        search: (query, searchCollection) =>
          unless query
            if $scope.inSearch
              $location.path('/viewer')
              $rootScope.$digest()
            return

          return unless annotator.discardDrafts()

          matched = []
          whole_document = true

          parsedQuery =
            text: ''
            tags: []

          for searchItem in searchCollection.models
            if searchItem.attributes.category is 'scope' and
            searchItem.attributes.value is 'sidebar'
              whole_document = false

            category = searchItem.attributes.category
            value = searchItem.attributes.value

            # Stuff we need to collect
            if category in ['text', 'quote', 'user', 'time', 'group']
              parsedQuery[category] = value

            # Tags are specials, because we collect those into an array
            if searchItem.attributes.category is 'tag'
              parsedQuery.tags.push value.toLowerCase()

          if whole_document
            annotations = annotator.plugins.Store.annotations
          else
            annotations = $rootScope.annotations

          matchingIDs = viewFilter.filter annotations, parsedQuery

          # Set the path
          # TODO: do we really need this data in the location?
          search =
            whole_document : whole_document
            matched : matchingIDs
            in_body_text: parsedQuery.text
            quote: parsedQuery.quote
          $location.path('/page_search').search(search)

          unless $scope.inSearch # If we are entering search right now
            # Turn dynamic bucket mode off for host/guests
            for p in annotator.providers
              p.channel.notify
                method: 'setDynamicBucketMode'
                params: false

          $rootScope.$digest()

        facetMatches: (callback) =>
          if $scope.show_search
            return callback ['text','tag', 'quote', 'scope', 'group','time','user'], {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'group' then callback ['Public', 'Private']
            when 'scope' then callback ['sidebar', 'document']
            when 'time'
              callback ['5 min', '30 min', '1 hour', '12 hours', '1 day', '1 week', '1 month', '1 year'], {preserveOrder: true}
        clearSearch: (original) =>
          # Execute clearSearch's internal method for resetting search
          original()

          # If we are in a search view, then the act of leaving it
          # will trigger the route change watch, which will call
          # leaveSearch(). However, if we have not yet started searching,
          # (only opened the searcbar), no route change will happen,
          # so we will have to trigger the cleanup manually.
          $scope.leaveSearch() unless $scope.inSearch

          # Go to viewer
          $location.path('/viewer')

          $rootScope.$digest()

    if search_query.length > 0
      $timeout =>
        @visualSearch.searchBox.searchEvent('')
      , 1500

    $scope.reloadAnnotations = ->
      return unless annotator.plugins.Store
      $scope.$root.annotations = []
      annotator.threading.thread []
      annotator.threading.idTable = {}

      Store = annotator.plugins.Store
      annotations = Store.annotations.slice()

      # XXX: Hacky hacky stuff to ensure that any search requests in-flight
      # at this time have no effect when they resolve and that future events
      # have no effect on this Store. Unfortunately, it's not possible to
      # unregister all the events or properly unload the Store because the
      # registration loses the closure. The approach here is perhaps
      # cleaner than fishing them out of the jQuery private data.
      # * Overwrite the Store's handle to the annotator, giving it one
      #   with a noop `loadAnnotations` method.
      Store.annotator = loadAnnotations: angular.noop
      # * Make all api requests into a noop.
      Store._apiRequest = angular.noop
      # * Ignore pending searches
      Store._onLoadAnnotations = angular.noop
      # * Make the update function into a noop.
      Store.updateAnnotation = angular.noop
      # * Remove the plugin and re-add it to the annotator.
      delete annotator.plugins.Store
      annotator.addPlugin 'Store', annotator.options.Store

      # Even though most operations on the old Store are now noops the Annotator
      # itself may still be setting up previously fetched annotatiosn. We may
      # delete annotations which are later set up in the DOM again, causing
      # issues with the viewer and heatmap. As these are loaded, we can delete
      # them, but the threading plugin will get confused and break threading.
      # Here, we cleanup these annotations as they are set up by the Annotator,
      # preserving the existing threading. This is all a bit paranoid, but
      # important when many annotations are loading as authentication is
      # changing. It's all so ugly it makes me cry, though. Someone help
      # restore sanity?
      cleanup = (loaded) ->
        $timeout ->  # Give the threading plugin time to thread this annotation
          deleted = []
          for l in loaded
            if l in annotations
              # If this annotation still exists, we'll need to thread it again
              # since the delete will mangle the threading data structures.
              existing = annotator.threading.idTable[l.id]?.message
              annotator.deleteAnnotation(l)
              deleted.push l
              if existing
                annotator.plugins.Threading.thread existing
          annotations = (a for a in annotations when a not in deleted)
          if annotations.length is 0
            annotator.unsubscribe 'annotationsLoaded', cleanup
        , 10
      cleanup (a for a in annotations when a.thread)
      annotator.subscribe 'annotationsLoaded', cleanup

    $scope.$watch 'show_search', (value, old) ->
      if value and not old
        $timeout ->
          $element.find('.visual-search').find('input').last().focus()
        , 10


    $scope.initUpdater = ->
      filter =
        streamfilter
          .setPastDataNone()
          .setMatchPolicyIncludeAny()
          .addClause('/uri', 'one_of', Object.keys(annotator.plugins.Store.entities))
          .getFilter()

      streamerURI = baseURI.replace /\/\w+(\/?\??[^\/]*)\/?$/, '/__streamer__'
      $scope.updater = new SockJS streamerURI

      $scope.updater.onopen = =>
        sockmsg =
          filter: filter
          clientID: annotator.clientID
        #console.log sockmsg
        $scope.updater.send JSON.stringify sockmsg

      $scope.updater.onclose = =>
        $timeout $scope.initUpdater, 60000

      $scope.updater.onmessage = (msg) =>
        #console.log msg
        unless msg.data.type? and msg.data.type is 'annotation-notification'
          return
        data = msg.data.payload
        action = msg.data.options.action
        clientID = msg.data.options.clientID

        if clientID is annotator.clientID
          return

        unless data instanceof Array then data = [data]

        p = $scope.auth.persona
        user = if p? then "acct:" + p.username + "@" + p.provider else ''
        unless data instanceof Array then data = [data]

        if $scope.socialView.name is 'single-player'
          owndata = data.filter (d) -> d.user is user
          $scope.applyUpdates action, owndata
        else
          $scope.applyUpdates action, data

    $scope.markAnnotationUpdate = (data) =>
      for annotation in data
        # We need to flag the top level
        if annotation.references?
          container = annotator.threading.getContainer annotation.references[0]
          if container?.message?
            container.message._updatedAnnotation = true
            # Temporary workarund to force publish changes
            if annotator.plugins.Store?
              annotator.plugins.Store._onLoadAnnotations [container.message]
        else
          annotation._updatedAnnotation = true

    $scope.applyUpdates = (action, data) =>
      switch action
        when 'create'
          # XXX: Temporary workaround until solving the race condition for annotationsLoaded event
          # Between threading and bridge plugins
          for annotation in data
            annotator.plugins.Threading.thread annotation

          $scope.markAnnotationUpdate data

          $scope.$apply =>
            if annotator.plugins.Store?
              annotator.plugins.Store._onLoadAnnotations data
        when 'update'
          $scope.markAnnotationUpdate data
          annotator.plugins.Store._onLoadAnnotations data
        when 'delete'
          $scope.markAnnotationUpdate data
          for annotation in data
            container = annotator.threading.getContainer annotation.id
            if container.message
              # XXX: This is a temporary workaround until real client-side only
              # XXX: delete will be introduced
              index = annotator.plugins.Store.annotations.indexOf container.message
              annotator.plugins.Store.annotations[index..index] = [] if index > -1
              annotator.deleteAnnotation container.message

      # Finally blink the changed tabs
      $timeout =>
        for p in annotator.providers
          p.channel.notify
            method: 'updateHeatmap'

        for p in annotator.providers
          p.channel.notify
            method: 'blinkBuckets'
      , 500

    $timeout =>
      $scope.initUpdater()
    , 5000

class Annotation
  this.$inject = [
    '$element', '$location', '$rootScope', '$sce', '$scope', '$timeout',
    '$window',
    'annotator', 'baseURI', 'drafts'
  ]
  constructor: (
     $element,   $location,   $rootScope,   $sce,   $scope,   $timeout,
     $window,
     annotator,   baseURI,   drafts
  ) ->
    threading = annotator.threading
    $scope.action = 'create'
    $scope.editing = false

    $scope.cancel = ($event) ->
      $event?.stopPropagation()
      $scope.editing = false
      drafts.remove $scope.model

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model
        else
          $scope.model.text = $scope.origText
          $scope.model.tags = $scope.origTags
          $scope.action = 'create'

    $scope.save = ($event) ->
      $event?.stopPropagation()
      annotation = $scope.model

      # Forbid saving comments without a body (text or tags)
      if annotator.isComment(annotation) and not annotation.text and
      not annotation.tags?.length
        $window.alert "You can not add a comment without adding some text, or at least a tag."
        return

      # Forbid the publishing of annotations
      # without a body (text or tags)
      if $scope.form.privacy.$viewValue is "Public" and
          not annotation.text and not annotation.tags?.length
        $window.alert "You can not make this annotation public without adding some text, or at least a tag."
        return

      $scope.rebuildHighlightText()

      $scope.editing = false
      drafts.remove annotation

      switch $scope.action
        when 'create'
          if annotator.isComment(annotation) and
              $rootScope.view isnt "Comments"
            $rootScope.applyView "Comments"
          if not annotator.isComment(annotation) and
              $rootScope.view is "Comments"
            $rootScope.applyView "Screen"
          $timeout (-> annotator.publish 'annotationCreated', annotation),
            1000
        when 'delete'
          root = $scope.$root.annotations
          root = (a for a in root when a isnt root)
          annotation.deleted = true
          unless annotation.text? then annotation.text = ''
          annotator.updateAnnotation annotation
        else
          annotator.updateAnnotation annotation

    $scope.reply = ($event) ->
      $event?.stopPropagation()
      unless annotator.plugins.Auth? and annotator.plugins.Auth.haveValidToken()
        $window.alert "In order to reply, you need to sign in."
        return

      references =
        if $scope.thread.message.references
          [$scope.thread.message.references..., $scope.thread.message.id]
        else
          [$scope.thread.message.id]

      reply =
        references: references
        uri: $scope.thread.message.uri

      annotator.publish 'beforeAnnotationCreated', [reply]
      drafts.add reply
      return

    $scope.edit = ($event) ->
      $event?.stopPropagation()
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.text
      $scope.origTags = $scope.model.tags
      drafts.add $scope.model, -> $scope.cancel()
      return

    $scope.delete = ($event) ->
      $event?.stopPropagation()
      replies = $scope.thread.children?.length or 0

      # We can delete the annotation if it hasn't got any replies or it is
      # private. Otherwise, we ask for a redaction message.
      if replies == 0 or $scope.form.privacy.$viewValue is 'Private'
        # If we're deleting it without asking for a message, confirm first.
        if confirm "Are you sure you want to delete this annotation?"
          if $scope.form.privacy.$viewValue is 'Private' and replies
            #Cascade delete its children
            for reply in $scope.thread.flattenChildren()
              if annotator.plugins?.Permissions? and
              annotator.plugins.Permissions.authorize 'delete', reply
                annotator.deleteAnnotation reply

          annotator.deleteAnnotation $scope.model
      else
        $scope.action = 'delete'
        $scope.editing = true
        $scope.origText = $scope.model.text
        $scope.origTags = $scope.model.tags
        $scope.model.text = ''
        $scope.model.tags = ''

    $scope.$watch 'editing', -> $scope.$emit 'toggleEditing'

    $scope.$watch 'model.id', (id) ->
      if id?
        $scope.thread = $scope.model.thread

        # Check if this is a brand new annotation
        if drafts.contains $scope.model
          $scope.editing = true


        # XXX: This should be done some other way since we should not assume
        # the annotation share URL is in any particular path relation to the
        # app base URL. It's time to start reflecting routes, I think. I'm
        # just not sure how best to do that with pyramid traversal since there
        # is not a pre-determined route map. One possibility would be to
        # unify everything so that it's relative to the app URL.
        prefix = baseURI.replace /\/\w+\/?$/, ''
        $scope.shared_link = prefix + '/a/' + $scope.model.id

    $scope.$watch 'model.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false

    $scope.$watch 'shared', (newValue) ->
      if newValue? is true
        $timeout -> $element.find('input').focus()
        $timeout -> $element.find('input').select()
        $scope.shared = false
        return

    $scope.$watchCollection 'model.thread.children', (newValue=[]) ->
      return unless $scope.model
      replies = (r.message for r in newValue)
      replies = replies.sort(annotator.sortAnnotations).reverse()
      $scope.model.reply_list = replies

    $scope.toggle = ->
      $element.find('.share-dialog').slideToggle()
      return

    $scope.share = ($event) ->
      $event.stopPropagation()
      return if $element.find('.share-dialog').is ":visible"
      $scope.shared = not $scope.shared
      $scope.toggle()
      return

    $scope.rebuildHighlightText = ->
      if annotator.text_regexp?
        $scope.model.highlightText = $scope.model.text
        for regexp in annotator.text_regexp
          $scope.model.highlightText =
            $scope.model.highlightText.replace regexp, annotator.highlighter


class Editor
  this.$inject = [
    '$location', '$routeParams', '$sce', '$scope',
    'annotator'
  ]
  constructor: (
     $location,   $routeParams,   $sce,   $scope,
     annotator
  ) ->
    {providers} = annotator

    save = ->
      $location.path('/viewer').search('id', $scope.annotation.id).replace()
      for p in providers
        p.channel.notify method: 'onEditorSubmit'
        p.channel.notify method: 'onEditorHide'

    cancel = ->
      $location.path('/viewer').search('id', null).replace()
      for p in providers
        p.channel.notify method: 'onEditorHide'

    $scope.action = if $routeParams.action? then $routeParams.action else 'create'
    if $scope.action is 'create'
      annotator.subscribe 'annotationCreated', save
      annotator.subscribe 'annotationDeleted', cancel
    else
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.subscribe 'annotationUpdated', save

    $scope.$on '$destroy', ->
      if $scope.action is 'edit' or $scope.action is 'redact'
        annotator.unsubscribe 'annotationUpdated', save
      else
        if $scope.action is 'create'
          annotator.unsubscribe 'annotationCreated', save
          annotator.unsubscribe 'annotationDeleted', cancel

    $scope.annotation = annotator.ongoing_edit

    delete annotator.ongoing_edit

    $scope.$watch 'annotation.target', (targets) ->
      return unless targets
      for target in targets
        if target.diffHTML?
          target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
          target.showDiff = not target.diffCaseOnly
        else
          delete target.trustedDiffHTML
          target.showDiff = false


class Viewer
  this.$inject = [
    '$location', '$rootScope', '$routeParams', '$scope',
    'annotator'
  ]
  constructor: (
    $location, $rootScope, $routeParams, $scope,
    annotator
  ) ->
    {providers, threading} = annotator
    $scope.sort = 'Newest'
    $scope.views = [
        {view:'Screen'}
        {view:'Document'}
        {view:"Comments"}
    ]

    $scope.sorts = [
        {sort:'Newest'}
        {sort:'Oldest'}
        {sort:'Location'}]
    $scope.predicate = 'updated'
    $scope.reverse = true
    $scope.hidden = 'hidden'
    # $scope.xhover = false

    $scope.$watch 'show_search', (newValue, oldValue) ->
      if newValue
        $scope.hidden = ''
      else
        $scope.hidden = 'hidden'

    $scope.$watch 'xhover', (newValue, oldValue) ->
      if newValue == true
        $scope.hidden = ''
      if newValue == false
        if $scope.show_search == false
          $scope.hidden = 'hidden'

    $scope.focus = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in providers
        p.channel.notify
          method: 'setActiveHighlights'
          params: highlights

    $scope.openDetails = (annotation) ->
      for p in providers
        p.channel.notify
          method: 'scrollTo'
          params: annotation.$$tag

    $rootScope.applyView = (view) ->
      switch view
        when 'Screen'
          # Go over all providers, and switch them to dynamic mode
          # They will, in turn, call back updateView
          # with the right set of annotations
          for p in providers
            p.channel.notify method: 'setDynamicBucketMode', params: true
          break

        when 'Document'
          for p in providers
            p.channel.notify method: 'showAll'
          break

        when 'Comments'
          for p in providers
            p.channel.notify method: 'showComments'

        else
          throw new Error "Unknown view requested: " + view

    $scope.applySort = (sort) ->
      $scope.sort = sort
      if $scope.sort == 'Newest'
        $scope.predicate = 'updated'
        $scope.reverse = true
      if $scope.sort == 'Oldest'
        $scope.predicate = 'updated'
        $scope.reverse = false
      if $scope.sort == 'Location'
        $scope.predicate = 'target[0].selector[2].start'
        $scope.reverse = false


class Search
  this.$inject = ['$filter', '$location', '$rootScope', '$routeParams', '$sce', '$scope', 'annotator']
  constructor: ($filter, $location, $rootScope, $routeParams, $sce, $scope, annotator) ->
    {providers, threading} = annotator

    $scope.highlighter = '<span class="search-hl-active">$&</span>'
    $scope.filter_orderBy = $filter('orderBy')
    $scope.render_order = {}
    $scope.render_pos = {}
    $scope.ann_info =
      shown : {}
      show_quote: {}
      more_top : {}
      more_bottom : {}
      more_top_num : {}
      more_bottom_num: {}

    buildRenderOrder = (threadid, threads) =>
      unless threads?.length
        return

      sorted = $scope.filter_orderBy threads, $scope.sortThread, true
      for thread in sorted
        $scope.render_pos[thread.message.id] = $scope.render_order[threadid].length
        $scope.render_order[threadid].push thread.message.id
        buildRenderOrder(threadid, thread.children)

    setMoreTop = (threadid, annotation) =>
      unless annotation.id in $scope.search_filter
        return false

      result = false
      pos = $scope.render_pos[annotation.id]
      if pos > 0
        prev = $scope.render_order[threadid][pos-1]
        unless prev in $scope.search_filter
          result = true
      result

    setMoreBottom = (threadid, annotation) =>
      unless annotation.id in $scope.search_filter
        return false

      result = false
      pos = $scope.render_pos[annotation.id]

      if pos < $scope.render_order[threadid].length-1
        next = $scope.render_order[threadid][pos+1]
        unless next in $scope.search_filter
          result = true
      result

    $scope.focus = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      for p in providers
        p.channel.notify
          method: 'setActiveHighlights'
          params: highlights

    $scope.openDetails = (annotation) ->
      # Temporary workaround, until search result annotation card
      # scopes get their 'annotation' fields, too.
      return unless annotation
      for p in providers
        p.channel.notify
          method: 'scrollTo'
          params: annotation.$$tag

    refresh = =>
      $scope.search_filter = $routeParams.matched

      # Create the regexps for highlighting the matches inside the annotations' bodies
      $scope.text_tokens = $routeParams.in_body_text.split ' '
      $scope.text_regexp = []
      $scope.quote = $routeParams.quote
      $scope.quote_regexp = new RegExp($scope.quote ,"ig")
      for token in $scope.text_tokens
        regexp = new RegExp(token,"ig")
        $scope.text_regexp.push regexp
      # Saving the regexps and higlighter to the annotator for highlighttext regeneration
      annotator.text_regexp = $scope.text_regexp
      annotator.highlighter = $scope.highlighter

      threads = []
      roots = {}
      $scope.render_order = {}
      # Choose the root annotations to work with
      for id, thread of annotator.threading.idTable when thread.message?
        annotation = thread.message
        annotation_root = if annotation.references? then annotation.references[0] else annotation.id
        # Already handled thread
        if roots[annotation_root]? then continue

        if annotation.id in $scope.search_filter
          # We have a winner, let's put its root annotation into our list and build the rendering
          root_thread = annotator.threading.getContainer annotation_root
          threads.push root_thread
          $scope.render_order[annotation_root] = []
          buildRenderOrder(annotation_root, [root_thread])
          roots[annotation_root] = true

      # Re-construct exact order the annotation threads will be shown

      # Fill search related data before display
      # - add highlights
      # - populate the top/bottom show more links
      # - decide that by default the annotation is shown or hidden
      # - Open detail mode for quote hits
      for thread in threads
        thread.message.highlightText = thread.message.text
        if thread.message.id in $scope.search_filter
          $scope.ann_info.shown[thread.message.id] = true
          if thread.message.text?
            for regexp in $scope.text_regexp
              thread.message.highlightText = thread.message.highlightText.replace regexp, $scope.highlighter
        else
          $scope.ann_info.shown[thread.message.id] = false

        $scope.ann_info.more_top[thread.message.id] = setMoreTop(thread.message.id, thread.message)
        $scope.ann_info.more_bottom[thread.message.id] = setMoreBottom(thread.message.id, thread.message)

        if $scope.quote?.length > 0
          $scope.ann_info.show_quote[thread.message.id] = true
          for target in thread.message.target
            target.highlightQuote = $sce.trustAsHtml target.quote.replace $scope.quote_regexp, $scope.highlighter
            if target.diffHTML?
              target.trustedDiffHTML = $sce.trustAsHtml target.diffHTML
              target.showDiff = not target.diffCaseOnly
            else
              delete target.trustedDiffHTML
              target.showDiff = false
        else
          for target in thread.message.target
            target.highlightQuote = target.quote
          $scope.ann_info.show_quote[thread.message.id] = false


        children = thread.flattenChildren()
        if children?
          for child in children
            child.highlightText = child.text
            if child.id in $scope.search_filter
              $scope.ann_info.shown[child.id] = true
              for regexp in $scope.text_regexp
                child.highlightText = child.highlightText.replace regexp, $scope.highlighter
            else
              $scope.ann_info.shown[child.id] = false

            $scope.ann_info.more_top[child.id] = setMoreTop(thread.message.id, child)
            $scope.ann_info.more_bottom[child.id] = setMoreBottom(thread.message.id, child)

            $scope.ann_info.show_quote[child.id] = false


      # Calculate the number of hidden annotations for <x> more labels
      for threadid, order of $scope.render_order
        hidden = 0
        last_shown = null
        for id in order
          if id in $scope.search_filter
            if last_shown? then $scope.ann_info.more_bottom_num[last_shown] = hidden
            $scope.ann_info.more_top_num[id] = hidden
            last_shown = id
            hidden = 0
          else
            hidden += 1
        if last_shown? then $scope.ann_info.more_bottom_num[last_shown] = hidden

      $rootScope.search_annotations = threads
      $scope.threads = threads

    $scope.$on 'ReRenderPageSearch', refresh
    $scope.$on '$routeUpdate', refresh

    $scope.getThreadId = (id) ->
      thread = annotator.threading.getContainer id
      threadid = id
      if thread.message.references?
        threadid = thread.message.references[0]
      threadid

    $scope.clickMoreTop = (id, $event) ->
      $event?.stopPropagation()
      threadid = $scope.getThreadId id
      pos = $scope.render_pos[id]
      rendered = $scope.render_order[threadid]
      $scope.ann_info.more_top[id] = false

      pos -= 1
      while pos >= 0
        prev_id = rendered[pos]
        if $scope.ann_info.shown[prev_id]
          $scope.ann_info.more_bottom[prev_id] = false
          break
        $scope.ann_info.more_bottom[prev_id] = false
        $scope.ann_info.more_top[prev_id] = false
        $scope.ann_info.shown[prev_id] = true
        pos -= 1


    $scope.clickMoreBottom = (id, $event) ->
      $event?.stopPropagation()
      threadid = $scope.getThreadId id
      pos = $scope.render_pos[id]
      rendered = $scope.render_order[threadid]
      $scope.ann_info.more_bottom[id] = false

      pos += 1
      while pos < rendered.length
        next_id = rendered[pos]
        if $scope.ann_info.shown[next_id]
          $scope.ann_info.more_top[next_id] = false
          break
        $scope.ann_info.more_bottom[next_id] = false
        $scope.ann_info.more_top[next_id] = false
        $scope.ann_info.shown[next_id] = true
        pos += 1

    refresh()


class Notification
  this.inject = ['$scope']
  constructor: (
    $scope
  ) ->


angular.module('h.controllers', ['bootstrap', 'h.streamfilter'])
  .controller('AppController', App)
  .controller('AnnotationController', Annotation)
  .controller('EditorController', Editor)
  .controller('ViewerController', Viewer)
  .controller('SearchController', Search)
  .controller('NotificationController', Notification)
