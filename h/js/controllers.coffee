class App
  scope:
    frame:
      visible: false
    sheet:
      collapsed: true
      tab: null

  this.$inject = [
    '$element', '$filter', '$http', '$location', '$rootScope', '$scope', '$timeout',
    'annotator', 'authentication', 'drafts', 'flash'
  ]
  constructor: (
    $element, $filter, $http, $location, $rootScope, $scope, $timeout
    annotator, authentication, drafts, flash
  ) ->
    # Get the base URL from the base tag or the app location
    baseUrl = angular.element('head base')[0]?.href
    baseUrl ?= ($location.absUrl().replace $location.url(), '')

    # Strip an empty hash and end in exactly one slash
    baseUrl = baseUrl.replace /#$/, ''
    baseUrl = baseUrl.replace /\/*$/, '/'
    $scope.baseUrl = baseUrl

    {plugins, provider} = annotator
    heatmap = annotator.plugins.Heatmap
    dynamicBucket = true

    heatmap.element.bind 'click', =>
      return unless drafts.discard()
      $location.search('id', null).replace()
      dynamicBucket = true
      annotator.showViewer()
      heatmap.publish 'updated'
      $scope.$digest()

    heatmap.subscribe 'updated', =>
      elem = d3.select(heatmap.element[0])
      return unless elem?.datum()
      data = {highlights, offset} = elem.datum()
      tabs = elem.selectAll('div').data data
      height = $(window).outerHeight(true)
      pad = height * .2

      {highlights, offset} = elem.datum()

      visible = $scope.frame.visible
      if dynamicBucket and visible and $location.path() == '/viewer'
        bottom = offset + heatmap.element.height()
        annotations = highlights.reduce (acc, hl) =>
          if hl.offset.top >= offset and hl.offset.top <= bottom
            if hl.data not in acc
              acc.push hl.data
          acc
        , []
        annotator.showViewer annotations

      elem.selectAll('.heatmap-pointer')
        # Creates highlights corresponding bucket when mouse is hovered
        .on 'mousemove', (bucket) =>
          unless $location.path() == '/viewer' and $location.search()?.id?
            provider.notify
              method: 'setActiveHighlights'
              params: heatmap.buckets[bucket]?.map (a) => a.$$tag

        # Gets rid of them after
        .on 'mouseout', =>
          if $location.path() == '/viewer' and not $location.search()?.id?
            provider.notify method: 'setActiveHighlights'

        # Does one of a few things when a tab is clicked depending on type
        .on 'click', (bucket) =>
          d3.event.stopPropagation()

          # If it's the upper tab, scroll to next bucket above
          if heatmap.isUpper bucket
            threshold = offset + heatmap.index[0]
            next = highlights.reduce (next, hl) ->
              if next < hl.offset.top < threshold then hl.offset.top else next
            , 0
            provider.notify method: 'scrollTop', params: next - pad

          # If it's the lower tab, scroll to next bucket below
          else if heatmap.isLower bucket
            threshold = offset + heatmap.index[0] + height - pad
            next = highlights.reduce (next, hl) ->
              if threshold < hl.offset.top < next then hl.offset.top else next
            , Number.MAX_VALUE
            provider.notify method: 'scrollTop', params: next - pad

          # If it's neither of the above, load the bucket into the viewer
          else
            return unless drafts.discard()
            dynamicBucket = false
            $location.search({'id' : null })
            annotator.showViewer heatmap.buckets[bucket]
            $scope.$digest()

    $scope.$watch 'sheet.collapsed', (newValue) ->
      $scope.sheet.tab = if newValue then null else 'login'

    $scope.$watch 'sheet.tab', (tab) ->
      $timeout =>
        $element
        .find('form')
        .filter(-> this.name is tab)
        .find('input')
        .filter(-> this.type isnt 'hidden')
        .first()
        .focus()
      , 10

    $scope.$watch 'auth.personas', (newValue, oldValue) =>
      unless newValue?.length
        authentication.persona = null
        authentication.token = null

        # Leave Highlighting mode when logging out
        if $scope.highlightingMode
          $scope.toggleHighlightingMode()

    $scope.$watch 'auth.persona', (newValue, oldValue) =>
      if oldValue? and not newValue?
        # TODO: better knowledge of routes
        authentication.$logout => $scope.$broadcast '$reset'
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
        plugins.Auth.withToken plugins.Permissions._setAuthFromToken
      else
        plugins.Permissions.setUser(null)
        delete plugins.Auth

      $scope.reloadAnnotations()

      if newValue? and annotator.ongoing_edit
        $timeout =>
          annotator.clickAdder()
        , 500

      if newValue? and $scope.ongoingHighlightSwitch
        $timeout =>
          $scope.toggleHighlightingMode()
        , 500

    $scope.$watch 'socialView.name', (newValue, oldValue) ->
      return if newValue is oldValue
      console.log "Social View changed to '" + newValue + "'. Reloading annotations."
      $scope.reloadAnnotations()

    $scope.$watch 'frame.visible', (newValue) ->
      if newValue
        annotator.show()
        annotator.provider?.notify method: 'showFrame'
        $element.find('.topbar').find('.tri').attr('draggable', true)
      else
        $scope.sheet.collapsed = true
        annotator.hide()
        annotator.provider.notify method: 'setActiveHighlights'
        annotator.provider.notify method: 'hideFrame'
        $element.find('.topbar').find('.tri').attr('draggable', false)

    $scope.$watch 'sheet.collapsed', (newValue) ->
      $scope.sheet.tab = if newValue then null else 'login'

    $scope.$watch 'sheet.tab', (tab) ->
      $timeout =>
        $element
        .find('form')
        .filter(-> this.name is tab)
        .find('input')
        .filter(-> this.type isnt 'hidden')
        .first()
        .focus()
      , 10

    $scope.$on 'back', ->
      return unless drafts.discard()
      if $location.path() == '/viewer' and $location.search()?.id?
        $location.search('id', null).replace()
      else
        annotator.hide()

    $scope.$on 'showAuth', (event, show=true) ->
      angular.extend $scope.sheet,
        collapsed: !show
        tab: 'login'

    $scope.$on '$reset', => angular.extend $scope, @scope,
      auth: authentication
      socialView: annotator.socialView

    $scope.$on 'success', (event, action) ->
      if action == 'claim'
        $scope.sheet.tab = 'activate'

    $scope.$broadcast '$reset'

    # Update scope with auto-filled form field values
    $timeout ->
      for i in $element.find('input') when i.value
        $i = angular.element(i)
        $i.triggerHandler('change')
        $i.triggerHandler('input')
    , 200  # We hope this is long enough

    $scope.toggleAlwaysOnHighlights = ->
      $scope.alwaysOnMode = not $scope.alwaysOnMode
      provider.notify
        method: 'setAlwaysOnMode'
        params: $scope.alwaysOnMode

    $scope.highlightingMode = false

    $scope.toggleHighlightingMode = ->
      # Check login state first
      unless plugins.Auth? and plugins.Auth.haveValidToken()
        # If we are not logged in, start the auth process
        $scope.ongoingHighlightSwitch = true
        annotator.show()
        $scope.sheet.collapsed = false
        $scope.sheet.tab = 'login'
        return

      delete $scope.ongoingHighlightSwitch
      $scope.highlightingMode = not $scope.highlightingMode
      annotator.socialView.name =
        if $scope.highlightingMode then "single-player" else "none"
      provider.notify
        method: 'setHighlightingMode'
        params: $scope.highlightingMode

    $scope.createUnattachedAnnotation = ->
      console.log "Should create unattached annotation"

    # Searchbar initialization
    @user_filter = $filter('userName')
    search_query = ''
    unless typeof(localStorage) is 'undefined'
      search_query = localStorage.getItem("hyp_page_search_query")
      console.log 'Loading back search query: ' + search_query

    @visualSearch = VS.init
      container: $element.find('.visual-search')
      query: search_query
      callbacks:
        search: (query, searchCollection) =>
          unless query
            return

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

                when 'tag'
                  unless annotation.tags?
                    matches = false
                    break

                  found = false
                  for tag in annotation.tags
                    if tag_search is tag.toLowerCase()
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

          # Save query to localStorage
          unless typeof(localStorage) is 'undefined'
            try
              localStorage.setItem "hyp_page_search_query", query
            catch error
              console.warn 'Cannot save query to localStorage!'
              if error is DOMException.QUOTA_EXCEEDED_ERR
                console.warn 'localStorage quota exceeded!'

          # Set the path
          search =
            whole_document : whole_document
            matched : matched
            in_body_text: in_body_text
          $location.path('/page_search').search(search)
          $rootScope.$digest()

        facetMatches: (callback) =>
          if $scope.show_search
            return callback ['text','tag','scope', 'group','time','user'], {preserveOrder: true}
        valueMatches: (facet, searchTerm, callback) ->
          switch facet
            when 'group' then callback ['Public', 'Private']
            when 'area' then callback ['sidebar', 'document']
            when 'time'
              callback ['5 min', '30 min', '1 hour', '12 hours', '1 day', '1 week', '1 month', '1 year'], {preserveOrder: true}
        clearSearch: (original) =>
          $scope.show_search = false
          original()
          unless typeof(localStorage) is 'undefined'
            try
              localStorage.setItem "hyp_page_search_query", ""
            catch error
              console.warn 'Cannot save query to localStorage!'
              if error is DOMException.QUOTA_EXCEEDED_ERR
                console.warn 'localStorage quota exceeded!'
          $location.path('/viewer')
          $rootScope.$digest()

    if search_query.length > 0
      $timeout =>
        @visualSearch.searchBox.searchEvent('')
      , 1500

    $scope.reloadAnnotations = ->
      if annotator.plugins.Store?
        $scope.$root.annotations = []
        annotator.threading.thread []

        Store = annotator.plugins.Store
        annotations = Store.annotations
        annotator.plugins.Store.annotations = []
        annotator.deleteAnnotation a for a in annotations

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
        # * Remove the plugin and re-add it to the annotator.
        delete annotator.plugins.Store
        annotator.considerSocialView Store.options
        annotator.addStore Store.options

        href = annotator.plugins.Store.options.loadFromSearch.uri
        for uri in annotator.plugins.Document.uris()
          unless uri is href # Do not load the href again
            console.log "Also loading annotations for: " + uri
            annotator.plugins.Store.loadAnnotationsFromSearch uri: uri

class Annotation
  this.$inject = ['$element', '$location', '$scope', 'annotator', 'drafts', '$timeout', '$window']
  constructor: ($element, $location, $scope, annotator, drafts, $timeout, $window) ->
    threading = annotator.threading
    $scope.action = 'create'
    $scope.editing = false

    $scope.cancel = ->
      $scope.editing = false
      drafts.remove $scope.model.$modelValue

      switch $scope.action
        when 'create'
          annotator.deleteAnnotation $scope.model.$modelValue
        else
          $scope.model.$modelValue.text = $scope.origText
          $scope.model.$modelValue.tags = $scope.origTags
          $scope.action = 'create'

    $scope.save = ->
      annotation = $scope.model.$modelValue        

      # Forbid the publishing of annotations
      # without a body (text or tags)
      if $scope.form.privacy.$viewValue is "Public" and
          not annotation.text and not annotation.tags?.length
        $window.alert "You can not make this annotation public without adding some text, or at least a tag."
        return

      $scope.editing = false
      drafts.remove annotation

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

    $scope.reply = ->
      unless annotator.plugins.Auth? and annotator.plugins.Auth.haveValidToken()
        $scope.$emit 'showAuth', true
        return

      references =
        if $scope.thread.message.references
          [$scope.thread.message.references..., $scope.thread.message.id]
        else
          [$scope.thread.message.id]

      reply = angular.extend annotator.createAnnotation(),
        references: references

      # XXX: This is ugly -- it's the one place we refer to the plugin directly
      annotator.plugins.Threading.thread reply

    $scope.edit = ->
      $scope.action = 'edit'
      $scope.editing = true
      $scope.origText = $scope.model.$modelValue.text
      $scope.origTags = $scope.model.$modelValue.tags

    $scope.delete = ->
      annotation = $scope.thread.message
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

    $scope.authorize = (action) ->
      if $scope.model.$modelValue? and annotator.plugins?.Permissions?
        annotator.plugins.Permissions.authorize action, $scope.model.$modelValue
      else
        true

    $scope.$on '$routeChangeStart', -> $scope.cancel() if $scope.editing
    $scope.$on '$routeUpdate', -> $scope.cancel() if $scope.editing

    $scope.$watch 'editing', -> $scope.$emit 'toggleEditing'

    $scope.$watch 'model.$modelValue.id', (id) ->
      if id?
        $scope.thread = threading.getContainer id

        # Check if this is a brand new annotation
        annotation = $scope.thread.message
        if annotation? and drafts.contains annotation
          $scope.editing = true

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

    $scope.toggle = ->
      $element.find('.share-dialog').slideToggle()

    $scope.share = ($event) ->
      $event.stopPropagation()
      $scope.shared = not $scope.shared
      $scope.toggle()

class Editor
  this.$inject = ['$location', '$routeParams', '$scope', 'annotator']
  constructor: ($location, $routeParams, $scope, annotator) ->
    save = ->
      $location.path('/viewer').search('id', $scope.annotation.id).replace()
      annotator.provider.notify method: 'onEditorSubmit'
      annotator.provider.notify method: 'onEditorHide'

    cancel = ->
      $location.path('/viewer').search('id', null).replace()
      annotator.provider.notify method: 'onEditorHide'

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


class Viewer
  this.$inject = [
    '$location', '$routeParams', '$scope',
    'annotator'
  ]
  constructor: (
    $location, $routeParams, $scope,
    annotator
  ) ->
    {provider, threading} = annotator

    $scope.focus = (annotation) ->
      if angular.isArray annotation
        highlights = (a.$$tag for a in annotation when a?)
      else if angular.isObject annotation
        highlights = [annotation.$$tag]
      else
        highlights = []
      provider.notify method: 'setActiveHighlights', params: highlights

    $scope.replies = (annotation) ->
      thread = threading.getContainer annotation.id
      (r.message for r in (thread.children or []))

    $scope.sortThread = (thread) ->
      if thread?.message?.updated
        return new Date(thread.message.updated)
      else
        return new Date()


class Search
  this.$inject = ['$filter', '$location', '$routeParams', '$scope', 'annotator']
  constructor: ($filter, $location, $routeParams, $scope, annotator) ->
    $scope.highlighter = '<span class="search-hl-active">$&</span>'
    $scope.filter_orderBy = $filter('orderBy')
    $scope.render_order = {}
    $scope.render_pos = {}
    $scope.ann_info =
      shown : {}
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

    refresh = =>
      $scope.search_filter = $routeParams.matched
      heatmap = annotator.plugins.Heatmap

      # Create the regexps for highlighting the matches inside the annotations' bodies
      $scope.text_tokens = $routeParams.in_body_text.split ' '
      $scope.text_regexp = []
      for token in $scope.text_tokens
        regexp = new RegExp(token,"ig")
        $scope.text_regexp.push regexp

      threads = []
      $scope.render_order = {}
      # Choose the root annotations to work with
      for bucket in heatmap.buckets
        for annotation in bucket
          # The annotation itself is a hit.
          thread = annotator.threading.getContainer annotation.id

          if annotation.id in $scope.search_filter
            threads.push thread
            $scope.render_order[annotation.id] = []
            buildRenderOrder(annotation.id, [thread])
            continue

          # Maybe it has a child we were looking for
          children = thread.flattenChildren()
          has_search_result = false
          if children?
            for child in children
              if child.id in $scope.search_filter
                has_search_result = true
                break

          if has_search_result
            threads.push thread
            $scope.render_order[annotation.id] = []
            buildRenderOrder(annotation.id, [thread])

      # Re-construct exact order the annotation threads will be shown

      # Fill search related data before display
      # - add highlights
      # - populate the top/bottom show more links
      # - decide that by default the annotation is shown or hidden
      for thread in threads
        thread.message.highlightText = thread.message.text
        if thread.message.id in $scope.search_filter
          $scope.ann_info.shown[thread.message.id] = true
          for regexp in $scope.text_regexp
            thread.message.highlightText = thread.message.highlightText.replace regexp, $scope.highlighter
        else
          $scope.ann_info.shown[thread.message.id] = false

        $scope.ann_info.more_top[thread.message.id] = setMoreTop(thread.message.id, thread.message)
        $scope.ann_info.more_bottom[thread.message.id] = setMoreBottom(thread.message.id, thread.message)

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


      $scope.threads = threads

    $scope.$on '$routeUpdate', refresh

    $scope.getThreadId = (id) ->
      thread = annotator.threading.getContainer id
      threadid = id
      if thread.message.references?
        threadid = thread.message.references[0]
      threadid

    $scope.clickMoreTop = (id) ->
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


    $scope.clickMoreBottom = (id) ->
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


    $scope.sortThread = (thread) ->
      if thread?.message?.updated
        return new Date(thread.message.updated)
      else
        return new Date()

    refresh()


angular.module('h.controllers', ['bootstrap'])
  .controller('AppController', App)
  .controller('AnnotationController', Annotation)
  .controller('EditorController', Editor)
  .controller('ViewerController', Viewer)
  .controller('SearchController', Search)
