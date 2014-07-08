formValidate = ->
  link: (scope, elem, attr, form) ->
    errorClassName = attr.formValidateErrorClass

    toggleClass = (field, {addClass}) ->
      fieldEl = elem.find("[data-target=#{field.$name}]")
      fieldEl.toggleClass(errorClassName, addClass)

    updateField = (field) ->
      return unless field?

      if field.$valid
        toggleClass(field, addClass: false)
      else
        toggleClass(field, addClass: true)

    # A custom parser for each form field that is used to reset the "response"
    # error state whenever the $viewValue changes.
    fieldParser = (field, value) ->
      field.$setValidity('response', true)
      updateField(field) if field.$valid
      return value

    forEachField = (fn) ->
      fn(field) for own _, field of form when field?.$name?

    forEachField (field) ->
      parser = angular.bind(null, fieldParser, field)
      field.$parsers.push(parser)

    # Validate field when the content changes.
    elem.on 'change', ':input', ->
      updateField(form[this.name])

    # Validate the field when submit is clicked.
    elem.on 'submit', (event) ->
      forEachField(updateField)

    # Validate when a response is processed.
    scope.$on 'error', (event, name) ->
      return unless form.$name == name
      forEachField(updateField)

  require: 'form'


markdown = ['$filter', '$timeout', ($filter, $timeout) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    input = elem.find('textarea')
    output = elem.find('div')

    # Re-render the markdown when the view needs updating.
    ctrl.$render = ->
      input.val (ctrl.$viewValue or '')
      scope.rendered = ($filter 'converter') (ctrl.$viewValue or '')

    # React to the changes to the text area
    input.bind 'blur change keyup', ->
      ctrl.$setViewValue input.val()
      scope.$digest()

    # Auto-focus the input box when the widget becomes editable.
    # Re-render when it becomes uneditable.
    scope.$watch 'readonly', (readonly) ->
      ctrl.$render()
      unless readonly then $timeout -> input.focus()

  require: '?ngModel'
  restrict: 'E'
  scope:
    readonly: '@'
    required: '@'
  templateUrl: 'markdown.html'
]


privacy = ->
  levels = ['Public', 'Private']

  link: (scope, elem, attrs, controller) ->
    return unless controller?

    controller.$formatters.push (permissions) ->
      return unless permissions?

      if 'group:__world__' in (permissions.read or [])
        'Public'
      else
        'Private'

    controller.$parsers.push (privacy) ->
      return unless privacy?

      permissions = controller.$modelValue
      if privacy is 'Public'
        if permissions.read
          unless 'group:__world__' in permissions.read
            permissions.read.push 'group:__world__'
        else
          permissions.read = ['group:__world__']
      else
        read = permissions.read or []
        read = (role for role in read when role isnt 'group:__world__')
        permissions.read = read

      permissions

    controller.$render = ->
      scope.level = controller.$viewValue

    scope.levels = levels
    scope.setLevel = (level) ->
      controller.$setViewValue level
      controller.$render()
  require: '?ngModel'
  restrict: 'E'
  scope: {}
  templateUrl: 'privacy.html'


recursive = ['$compile', '$timeout', ($compile, $timeout) ->
  compile: (tElement, tAttrs, transclude) ->
    placeholder = angular.element '<!-- recursive -->'
    attachQueue = []
    tick = false

    template = tElement.contents().clone()
    tElement.html ''

    transclude = $compile template, (scope, cloneAttachFn) ->
      clone = placeholder.clone()
      cloneAttachFn clone
      $timeout ->
        transclude scope, (el, scope) -> attachQueue.push [clone, el]
        unless tick
          tick = true
          requestAnimationFrame ->
            tick = false
            for [clone, el] in attachQueue
              clone.after el
              clone.bind '$destroy', -> el.remove()
            attachQueue = []
      clone
    post: (scope, iElement, iAttrs, controller) ->
      transclude scope, (contents) -> iElement.append contents
  restrict: 'A'
  terminal: true
]


tabReveal = ['$parse', ($parse) ->
  compile: (tElement, tAttrs, transclude) ->
    panes = []
    hiddenPanesGet = $parse tAttrs.tabReveal

    pre: (scope, iElement, iAttrs, [ngModel, tabbable] = controller) ->
      # Hijack the tabbable controller's addPane so that the visibility of the
      # secret ones can be managed. This avoids traversing the DOM to find
      # the tab panes.
      addPane = tabbable.addPane
      tabbable.addPane = (element, attr) =>
        removePane = addPane.call tabbable, element, attr
        panes.push
          element: element
          attr: attr
        =>
          for i in [0..panes.length]
            if panes[i].element is element
              panes.splice i, 1
              break
          removePane()

    post: (scope, iElement, iAttrs, [ngModel, tabbable] = controller) ->
      tabs = angular.element(iElement.children()[0].childNodes)
      render = angular.bind ngModel, ngModel.$render

      ngModel.$render = ->
        render()
        hiddenPanes = hiddenPanesGet scope
        return unless angular.isArray hiddenPanes

        for i in [0..panes.length-1]
          pane = panes[i]
          value = pane.attr.value || pane.attr.title
          if value == ngModel.$viewValue
            pane.element.css 'display', ''
            angular.element(tabs[i]).css 'display', ''
          else if value in hiddenPanes
            pane.element.css 'display', 'none'
            angular.element(tabs[i]).css 'display', 'none'
  require: ['ngModel', 'tabbable']
]


thread = ['$rootScope', '$window', ($rootScope, $window) ->
  # Helper -- true if selection ends inside the target and is non-empty
  ignoreClick = (event) ->
    sel = $window.getSelection()
    if sel.focusNode?.compareDocumentPosition(event.target) & 8
      if sel.toString().length
        return true
    return false

  link: (scope, elem, attr, ctrl) ->
    childrenEditing = {}

    # If this is supposed to be focused, then open it
    if scope.annotation in ($rootScope.focused or [])
      scope.collapsed = false

    scope.$on "focusChange", ->
      # XXX: This not needed to be done when the viewer and search will be unified
      ann = scope.annotation ? scope.thread.message
      if ann in $rootScope.focused
        scope.collapsed = false
      else
        unless ann.references?.length
          scope.collapsed = true

    scope.toggleCollapsed = (event) ->
      event.stopPropagation()
      return if (ignoreClick event) or Object.keys(childrenEditing).length
      scope.collapsed = !scope.collapsed
      # XXX: This not needed to be done when the viewer and search will be unified
      ann = scope.annotation ? scope.thread.message
      if scope.collapsed
        $rootScope.unFocus ann, true
      else
        scope.openDetails ann
        $rootScope.focus ann, true

    scope.$on 'toggleEditing', (event) ->
      {$id, editing} = event.targetScope
      if editing
        scope.collapsed = false
        unless childrenEditing[$id]
          event.targetScope.$on '$destroy', ->
            delete childrenEditing[$id]
          childrenEditing[$id] = true
      else
        delete childrenEditing[$id]
  restrict: 'C'
]


repeatAnim = ->
  restrict: 'A'
  scope:
    array: '='
  template: '<div ng-init="runAnimOnLast()"><div ng-transclude></div></div>'
  transclude: true

  controller: ($scope, $element, $attrs) ->
    $scope.runAnimOnLast = ->
      #Run anim on the item's element
      #(which will be last child of directive element)
      item=$scope.array[0]
      itemElm = jQuery($element)
        .children()
        .first()
        .children()

      unless item._anim?
        return
      if item._anim is 'fade'
        itemElm
          .css({ opacity: 0 })
          .animate({ opacity: 1 }, 1500)
      else
        if item._anim is 'slide'
          itemElm
            .css({ 'margin-left': itemElm.width() })
            .animate({ 'margin-left': '0px' }, 1500)
      return

# Directive to edit/display a tag list.
tags = ['$window', ($window) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    elem.tagit
      caseSensitive: false
      placeholderText: attr.placeholder
      keepPlaceholder: true
      allowSpaces: true
      preprocessTag: (val) ->
        val.replace /[^a-zA-Z0-9\-\_\s]/g, ''
      afterTagAdded: (evt, ui) ->
        ctrl.$setViewValue elem.tagit 'assignedTags'
      afterTagRemoved: (evt, ui) ->
        ctrl.$setViewValue elem.tagit 'assignedTags'
      autocomplete:
        source: []
      onTagClicked: (evt, ui) ->
        evt.stopPropagation()
        tag = ui.tagLabel
        $window.open "/t/" + tag

    elem.find('input').addClass('form-input')

    ctrl.$formatters.push (tags=[]) ->
      assigned = elem.tagit 'assignedTags'
      for t in assigned when t not in tags
        elem.tagit 'removeTagByLabel', t
      for t in tags when t not in assigned
        elem.tagit 'createTag', t
      if assigned.length or not attr.readOnly then elem.show() else elem.hide()

    attr.$observe 'readonly', (readonly) ->
      tagInput = elem.find('input').last()
      assigned = elem.tagit 'assignedTags'
      if readonly
        tagInput.attr('disabled', true)
        tagInput.removeAttr('placeholder')
        if assigned.length then elem.show() else elem.hide()
      else
        tagInput.removeAttr('disabled')
        tagInput.attr('placeholder', attr['placeholder'])
        elem.show()

  require: '?ngModel'
  restrict: 'C'
]


username = ['$filter', '$window', ($filter, $window) ->
  link: (scope, elem, attr) ->
    scope.$watch 'user', ->
      scope.uname = $filter('persona')(scope.user, 'username')

    scope.uclick = (event) ->
      event.preventDefault()
      $window.open "/u/#{scope.uname}"
      return

  scope:
    user: '='
  restrict: 'E'
  template: '<span class="user" ng-click="uclick($event)">{{uname}}</span>'
]

fuzzytime = ['$filter', '$window', ($filter, $window) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    elem
    .find('a')
    .bind 'click', (event) ->
      event.stopPropagation()
    .tooltip
      tooltipClass: 'small'
      position:
        collision: 'fit'
        at: "left center"

    ctrl.$render = ->
      scope.ftime = ($filter 'fuzzyTime') ctrl.$viewValue

      # Determining the timezone name
      timezone = jstz.determine().name()
      # The browser language
      userLang = navigator.language || navigator.userLanguage

      # Now to make a localized hint date, set the language
      momentDate = moment ctrl.$viewValue
      momentDate.lang(userLang)

      # Try to localize to the browser's timezone
      try
        scope.hint = momentDate.tz(timezone).format('LLLL')
      catch error
        # For invalid timezone, use the default
        scope.hint = momentDate.format('LLLL')

      toolparams =
        tooltipClass: 'small'
        position:
          collision: 'none'
          at: "left center"


      elem.tooltip(toolparams)

    timefunct = ->
      $window.setInterval =>
        scope.ftime = ($filter 'fuzzyTime') ctrl.$viewValue
        scope.$digest()
      , 5000

    scope.timer = timefunct()

    scope.$on '$destroy', ->
      $window.clearInterval scope.timer

  require: '?ngModel'
  restrict: 'E'
  scope: true
  template: '<a target="_blank" href="{{shared_link}}" title="{{hint}}">{{ftime | date:mediumDate}}</a>'
]

whenscrolled = ->
  link: (scope, elem, attr) ->
    elem.bind 'scroll', ->
      {clientHeight, scrollHeight, scrollTop} = elem[0]
      if scrollHeight - scrollTop <= clientHeight + 40
        scope.$apply attr.whenscrolled

match = ->
  # Checks to see if two values match each other.
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    elem
    .on 'keyup', ->
      currentValue = scope.match == ctrl.$modelValue
      ctrl.$setValidity('match', currentValue)

  scope:
    match: '='
  restrict: 'A'
  require: 'ngModel'

confirmPasswordCheck = ['$resource', ($resource)->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?
    # Check password against server.
  restrict: 'A'
  require: 'ngModel'
]

panels = ->
  # This panels directive houses panels in the sidebar (such as settings, accountmanagement, etc). Each panel is it's own directive.
  link: (scope, elem, attr, ctrl) ->
    scope.togglePanels = (panel)->
      scope.activePanel.active = !scope.activePanel.active
      scope.activePanel = panel
      scope.activePanel.active = !scope.activePanel.active

  # Ujvari, you may want to move this to the controllers.coffee file.
  controller: ($scope, $rootScope, $filter, $element) ->
    $rootScope.showPanels = false

    # Toggles Panels shown or hidden.
    $rootScope.toggleShowPanels = ->
      $rootScope.showPanels = !$rootScope.showPanels
      $rootScope.viewState.showControls = false

    # This is the list of panels that will be shown. In the panels.html template
    # there are elements with ng-show on them, for example:
    #     <div ng-show="activePanel.name == 'Notifications'">
    #     My Html for a new panel.
    #     </div>
    $scope.panelList = [
      # {name:"Profile", active: true, icon:"user-icon"}
      {name:"Account", active: false, icon:"plus-icon"}
      # {name:"Settings", active: false, icon:"cog-icon"}
    ]
    $scope.activePanel = $scope.panelList[0]

  restrict: 'C'
  templateUrl: 'panels.html'

accountManagement = ['$filter', 'flash', 'session', ($filter, flash, session) ->
  link: (scope, elem, attr, ctrl) ->
    scope.emailCheck = ->
      # Checks to see if email is duplicate.
      return
  controller: ($scope, $filter) ->
    persona_filter = $filter('persona')

    _answer = ->
      console.log '_answer() - insert code here'

    _error = (errors={}) ->
      for field, error of errors
        console.log(field, error)
        flash('error', error)

    $scope.confirmDelete = false
    $scope.toggleConfirmDelete = ->
      $scope.confirmDelete = !$scope.confirmDelete

    $scope.deleteAcount = (form) ->
      # If the password is correct, the account is deleted.
      # The extension is then removed from the page.
      # Confirmation of success is given.
      alert("Account deleted.")

    $scope.submit = (form) ->
      # In the frontend change_email and change_password are two different
      # forms. However, in the backend it is just one: edit_profile
      $scope.model.username = persona_filter $scope.model.persona
      $scope.model.formname = form.$name
      angular.extend session, $scope.model
      return unless form.$valid
      promise = session["$edit_profile"] ->
        $scope.$emit 'success', form.$name
      promise.then(_answer, _error)


    # Jake's Note: there is an addional piece of UI I would like to implement. The basic idea being
    # to give some visual indication that the changes they have made have been applied successfully.
    # If they change their email, it would be nice to have an event (or something) to tell the front end that
    # the request was successful.

  restrict: 'C'
  templateUrl: 'accountmanagement.html'
]

accountProfile = ->
  # This is the acount profile stuff that will eventually be outside of the settings panel.
  # Rational for keeping it in the settings panel (temporarily):
  # 1. We might as well write the back end for this stuff, then when I do the front end stuff for profiles we'll
  #    have the backend work started.
  # 2. As a directive it is extremely easy to move this around and get it out of the side bar.
  link: (scope, elem, attr, ctrl) ->
    scope.editProfile = ->
      # Switches profile into edit mode.
      return
  controller: ($scope) ->
    $scope.demoData =
      # Is there any thing else we should be collecting for now?
      name : "Jake Hartnell"
      password : "password"
      location : "Berkeley, CA"
      bio : "A short bio..."
      website : "http://jakehartnell.com"
      gravatar : ""
  restrict: 'C'
  templateUrl: 'profile.html'

settings = ->
  # Question: Should each setting be it's own directive?
  link: (scope, elem, attr, ctrl) ->
    return
  controller: ($scope) ->
    return
  restrict: 'C'
  templateUrl: 'settings.html'


angular.module('h.directives', ['ngSanitize'])
<<<<<<< HEAD
.directive('formValidate', formValidate)
.directive('fuzzytime', fuzzytime)
.directive('markdown', markdown)
.directive('privacy', privacy)
.directive('recursive', recursive)
.directive('tabReveal', tabReveal)
.directive('tags', tags)
.directive('thread', thread)
.directive('username', username)
.directive('repeatAnim', repeatAnim)
.directive('whenscrolled', whenscrolled)
.directive('panels', panels)
.directive('match', match)
.directive('confirmPasswordCheck', confirmPasswordCheck)
.directive('accountManagement', accountManagement)
.directive('accountProfile', accountProfile)
.directive('settings', settings)
