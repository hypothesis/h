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


###
# The slow validation directive ties an to a model controller and hides
# it while the model is being edited. This behavior improves the user
# experience of filling out forms by delaying validation messages until
# after the user has made a mistake.
###
slowValidate = ->
  link: (scope, elem, attr, ctrl) ->
    fieldName = attr.slowValidate
    return unless ctrl.$name? and ctrl?[fieldName]

    elem.addClass 'slow-validate'

    fieldPath = [ctrl.$name, fieldName, '$viewValue'].join('.')
    modelCtrl = ctrl?[fieldName]

    scope.$watch fieldPath, ->
      if modelCtrl.$invalid and modelCtrl.$dirty
        elem.addClass 'slow-validate-show'
      else
        elem.removeClass 'slow-validate-show'

  require: '^form'
  restrict: 'A'


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


userPicker = ->
  restrict: 'ACE'
  scope:
    model: '=userPickerModel'
    options: '=userPickerOptions'
  templateUrl: 'userPicker.html'

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
      scope.provider = $filter('persona')(scope.user, 'provider')

    scope.uclick = (event) ->
      event.preventDefault()
      $window.open "/u/#{scope.uname}@#{scope.provider}"
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


visualSearch = ['$parse', ($parse) ->
  link: (scope, elem, attr, ctrl) ->
    _search = $parse(attr.onsearch)
    _clear = $parse(attr.onclear)
    _facets = $parse(attr.facets)
    _values = $parse(attr.values)

    _vs = VS.init
      container: elem
      callbacks:
        search: (query, modelCollection) ->
          scope.$apply ->
            _search(scope, {"this": modelCollection})
        clearSearch: (original) ->
          _vs.searchBox.value('')
          if attr.onclear
            scope.$apply ->
              _clear(scope)
          else
            original()
        facetMatches: (callback) ->
          facets = _facets(scope) or []
          callback(facets or [], preserveOrder: true)
        valueMatches: (facet, term, callback) ->
          values = _values(scope)?[facet]
          callback(values or [], preserveOrder: true)

    scope.$watch attr.query, (query) ->
      p = 0
      _vs.searchBox.value('')
      for k, values of query
        continue unless values?.length
        unless angular.isArray values then values = [values]
        for v in values
          _vs.searchBox.addFacet(k, v, p++)
      _search(scope, {"this": _vs.searchQuery})

  restrict: 'C'
]

whenscrolled = ['$window', ($window) ->
  link: (scope, elem, attr) ->
    $window = angular.element($window)
    $window.on 'scroll', ->
      windowBottom = $window.height() + $window.scrollTop()
      elementBottom = elem.offset().top + elem.height()
      if elementBottom > 0 and elementBottom - windowBottom <= 0
        scope.$apply attr.whenscrolled
]

validateForm = ['$parse', ($parse) ->
  require: 'form',
  link: (scope, elem, attr, formController) ->
    onSuccess = $parse(attr.validateForm)
    touchedInputs = {} # Inputs that the user has blurred.

    scope.isFieldValid = (fieldName) ->
      field = formController[fieldName]
      unless field
        throw new Error("The #{field} field could not be found on this form")
      touchedInputs[fieldName] && field.$dirty && field.$invalid

    scope.fieldClass = (fieldName, defaults, error) ->
      if scope.isFieldValid(fieldName) then "#{defaults} #{error}" else defaults

    elem.on 'submit', (event) ->
      Object.keys(formController).forEach (prop) ->
        if prop.indexOf('$') != 0
          formController[prop].$dirty = true
          touchedInputs[prop] = true

    elem.on 'blur', ':input', ->
      touchedInputs[this.name] = true
      scope.$apply()
]

angular.module('h.directives', ['ngSanitize'])
.directive('fuzzytime', fuzzytime)
.directive('markdown', markdown)
.directive('privacy', privacy)
.directive('recursive', recursive)
.directive('slowValidate', slowValidate)
.directive('tabReveal', tabReveal)
.directive('tags', tags)
.directive('thread', thread)
.directive('username', username)
.directive('userPicker', userPicker)
.directive('repeatAnim', repeatAnim)
.directive('visualSearch', visualSearch)
.directive('whenscrolled', whenscrolled)
.directive('validateForm', validateForm)
