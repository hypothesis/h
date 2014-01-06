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
    'annotator', 'authentication', 'streamfilter'
  ]
  constructor: (
    $element, $filter, $http, $location, $rootScope, $scope, $timeout
    annotator, authentication, streamfilter
  ) ->
    # Get the base URL from the base tag or the app location
    baseUrl = angular.element('head base')[0]?.href
    baseUrl ?= ($location.absUrl().replace $location.url(), '')

    # Strip an empty hash and end in exactly one slash
    baseUrl = baseUrl.replace /#$/, ''
    baseUrl = baseUrl.replace /\/*$/, '/'
    $scope.baseUrl = baseUrl

    {plugins, host, providers} = annotator

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
        else
          $scope.auth.persona = oldValue
      else if newValue?
        $scope.sheet.collapsed = true

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

    @user_filter = $filter('userName')
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
          in_body_text = ''
          for searchItem in searchCollection.models
            if searchItem.attributes.category is 'scope' and
            searchItem.attributes.value is 'sidebar'
              whole_document = false

            if searchItem.attributes.category is 'text'
              in_body_text = searchItem.attributes.value.toLowerCase()
              text_tokens = searchItem.attributes.value.split ' '
            if searchItem.attributes.category is 'tag'
              tag_search = searchItem.attributes.value.toLowerCase()
            if searchItem.attributes.category is 'quote'
              quote_search = searchItem.attributes.value.toLowerCase()

          if whole_document
            annotations = annotator.plugins.Store.annotations
          else
            annotations = $rootScope.annotations

          for annotation in annotations
            matches = true
            for searchItem in searchCollection.models
              category = searchItem.attributes.category
              value = searchItem.attributes.value
              switch category
                when 'user'
                  userName = @user_filter annotation.user
                  unless userName.toLowerCase() is value.toLowerCase()
                    matches = false
                    break
                when 'text'
                  unless annotation.text?
                    matches = false
                    break
                  for token in text_tokens
                    unless annotation.text.toLowerCase().indexOf(token.toLowerCase()) > -1
                      matches = false
                      break
                when 'quote'
                  # Reply annotations does not have a quote in this aspect
                  if annotation.references?
                      matches = false
                      break
                  else
                    found = false
                    for target in annotation.target
                      if target.quote? and target.quote.toLowerCase().indexOf(quote_search) > -1
                        found = true
                        break
                    unless found
                      matches = false
                      break
                when 'tag'
                  unless annotation.tags?
                    matches = false
                    break
                  found = false
                  for tag in annotation.tags
                    if tag.toLowerCase().indexOf(tag_search) > -1
                      found = true
                      break
                  unless found
                    matches = false
                  break
                when 'time'
                    delta = Math.round((+new Date - new Date(annotation.updated)) / 1000)
                    switch value
                      when '5 min'
                        unless delta <= 60*5
                          matches = false
                      when '30 min'
                        unless delta <= 60*30
                          matches = false
                      when '1 hour'
                        unless delta <= 60*60
                          matches = false
                      when '12 hours'
                        unless delta <= 60*60*12
                          matches = false
                      when '1 day'
                        unless delta <= 60*60*24
                          matches = false
                      when '1 week'
                        unless delta <= 60*60*24*7
                          matches = false
                      when '1 month'
                        unless delta <= 60*60*24*31
                          matches = false
                      when '1 year'
                        unless delta <= 60*60*24*366
                          matches = false
                when 'group'
                    priv_public = 'group:__world__' in (annotation.permissions.read or [])
                    switch value
                      when 'Public'
                        unless priv_public
                          matches = false
                      when 'Private'
                        if priv_public
                          matches = false

            if matches
              matched.push annotation.id

          # Set the path
          search =
            whole_document : whole_document
            matched : matched
            in_body_text: in_body_text
            quote: quote_search
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
      $scope.new_updates = 0
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

    # Notifications
    $scope.notifications = []

    $scope.removeNotificationUpdate = ->
      index = -1
      for notif in $scope.notifications
        if notif.type is 'update'
          index = $scope.notifications.indexOf notif
          break

      if index > -1 then $scope.notifications.splice index,1

    $scope.addUpdateNotification = ->
      # Do not add an update notification twice
      unless $scope.new_updates > 0
        if $scope.new_updates < 2 then text = 'change.'
        else text = 'changes.'
        notification =
          type: 'update'
          text: 'Click to load ' + $scope.new_updates + ' ' + text
          callback: =>
            $scope.reloadAnnotations()
            $scope.removeNotificationUpdate()
          close: $scope.removeNotificationUpdate

        $scope.notifications.unshift notification

    $scope.$watch 'new_updates', (updates, oldUpdates) ->
      return unless updates or oldUpdates

      for notif in $scope.notifications
        if notif.type is 'update'
          if $scope.new_updates < 2 then text = 'change.'
          else text = 'changes.'
          notif.text = 'Click to load ' + updates + ' ' + text

      for p in annotator.providers
        p.channel.notify
          method: 'updateNotificationCounter'
          params: updates

    $scope.$watch 'show_search', (value, old) ->
      if value and not old
        $timeout ->
          $element.find('.visual-search').find('input').last().focus()
        , 10


    $scope.initUpdater = ->
      $scope.new_updates = 0
      # Quick hack until we unify all the routes.
      # We need to eliminate the distinction between the app and the site
      # because it's not useful. The site is the app, stupid!
      # Then everything will be relative to the same base.
      path = $scope.baseUrl.replace(/\/\w+\/$/, '/')
      path = "#{path}__streamer__"

      # Collect all uris we should watch
      uris = (e for e of annotator.plugins.Store.entities).join ','

      filter =
        streamfilter
          .setPastDataNone()
          .setMatchPolicyIncludeAny()
          .setClausesParse('uri:[' + uris)
          .getFilter()

      $scope.updater = new SockJS(path)

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
        $scope.$apply =>
          if data.length > 0 then $scope.new_updates += 1

        if $scope.socialView.name is 'single-player'
          owndata = data.filter (d) -> d.user is user
          $scope.applyUpdates action, owndata
        else
          $scope.applyUpdates action, data

    $scope.applyUpdates = (action, data) =>
      switch action
        when 'create'
          $scope.$apply =>
            if annotator.plugins.Store?
              annotator.plugins.Store._onLoadAnnotations data
        when 'update'
          if annotator.plugins.Store?
            annotator.plugins.Store._onLoadAnnotations data
        when 'delete'
          console.log 'deleted'

    $timeout =>
      $scope.initUpdater()
    , 5000

class Annotation
  this.$inject = ['$element', '$location', '$sce', '$scope', 'annotator', 'drafts', '$timeout', '$window']
  constructor: ($element, $location, $sce, $scope, annotator, drafts, $timeout, $window) ->
    threading = annotator.threading
    $scope.action = 'create'
    $scope.editing = false

    $scope.cancel = ($event) ->
      $event?.stopPropagation()
      $scope.editing = false
      drafts.remove $scope.model.$modelValue
      annotator.enableAnnotating drafts.isEmpty()

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model.$modelValue
        else
          $scope.model.$modelValue.text = $scope.origText
          $scope.model.$modelValue.tags = $scope.origTags
          $scope.action = 'create'

    $scope.save = ($event) ->
      $event?.stopPropagation()
      annotation = $scope.model.$modelValue

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
      annotator.enableAnnotating drafts.isEmpty()

      switch $scope.action
        when 'create'
          annotator.publish 'annotationCreated', annotation
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
      annotator.disableAnnotating()

    $scope.edit = ($event) ->
      $event?.stopPropagation()
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.$modelValue.text
      $scope.origTags = $scope.model.$modelValue.tags
      drafts.add $scope.model.$modelValue, -> $scope.cancel()
      annotator.disableAnnotating()

    $scope.delete = ($event) ->
      $event?.stopPropagation()
      annotation = $scope.model.$modelValue
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

          annotator.deleteAnnotation annotation
      else
        $scope.action = 'delete'
        $scope.editing = true
        $scope.origText = $scope.model.$modelValue.text
        $scope.origTags = $scope.model.$modelValue.tags
        $scope.model.$modelValue.text = ''
        $scope.model.$modelValue.tags = ''

    $scope.$watch 'editing', -> $scope.$emit 'toggleEditing'

    $scope.$watch 'model.$modelValue.id', (id) ->
      if id?
        annotation = $scope.model.$modelValue
        $scope.thread = annotation.thread

        # Check if this is a brand new annotation
        if annotation? and drafts.contains annotation
          $scope.editing = true

    $scope.$watch 'model.$modelValue.target', (targets) ->
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

        # XXX: This should be done some other way since we should not assume
        # the annotation share URL is in any particular path relation to the
        # app base URL. It's time to start reflecting routes, I think. I'm
        # just not sure how best to do that with pyramid traversal since there
        # is not a pre-determined route map. One possibility would be to
        # unify everything so that it's relative to the app URL.
        prefix = $scope.$parent.baseUrl.replace /\/\w+\/$/, ''
        $scope.shared_link = prefix + '/a/' + $scope.model.$modelValue.id
        $scope.shared = false

    $scope.$watchCollection 'model.$modelValue.thread.children', (newValue=[]) ->
      annotation = $scope.model.$modelValue
      return unless annotation

      replies = (r.message for r in newValue)
      replies = replies.sort(annotator.sortAnnotations).reverse()
      annotation.reply_list = replies

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
        $scope.model.$modelValue.highlightText = $scope.model.$modelValue.text
        for regexp in annotator.text_regexp
          $scope.model.$modelValue.highlightText =
            $scope.model.$modelValue.highlightText.replace regexp, annotator.highlighter


class Editor
  this.$inject = ['$location', '$routeParams', '$sce', '$scope', 'annotator']
  constructor: ($location, $routeParams, $sce, $scope, annotator) ->
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
