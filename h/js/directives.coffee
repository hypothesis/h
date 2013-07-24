authentication = ->
  base =
    username: null
    email: null
    password: null
    code: null

  link: (scope, elem, attr, ctrl) ->
    angular.extend scope, base
  controller: [
    '$scope', 'authentication',
    ($scope,   authentication) ->
      $scope.$on '$reset', => angular.extend $scope, base

      $scope.submit = (form) ->
        return unless form.$valid
        authentication["$#{form.$name}"] ->
          $scope.$emit 'success', form.$name
  ]
  scope:
    model: '=authentication'


markdown = ['$filter', '$timeout', ($filter, $timeout) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    input = elem.find('textarea')
    output = elem.find('div')

    # Re-render the markdown when the view needs updating.
    ctrl.$render = ->
      input.attr('value', ctrl.$viewValue or '')
      scope.rendered = ($filter 'converter') (ctrl.$viewValue or '')

    # React to the changes to the text area
    input.bind 'blur change keyup', ->
      ctrl.$setViewValue input[0].value
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

    scope.model = controller
    scope.levels = levels
  require: '?ngModel'
  restrict: 'E'
  scope: true
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


resettable = ->
  compile: (tElement, tAttrs, transclude) ->
    post: (scope, iElement, iAttrs) ->
      reset = ->
        transclude scope, (el) ->
          iElement.replaceWith el
          iElement = el
      reset()
      scope.$on '$reset', reset
  priority: 5000
  restrict: 'A'
  transclude: 'element'


###
# The slow validation directive ties an to a model controller and hides
# it while the model is being edited. This behavior improves the user
# experience of filling out forms by delaying validation messages until
# after the user has made a mistake.
###
slowValidate = ['$parse', '$timeout', ($parse, $timeout) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    promise = null

    elem.addClass 'slow-validate'

    ctrl[attr.slowValidate]?.$viewChangeListeners?.push (value) ->
      elem.removeClass 'slow-validate-show'

      if promise
        $timeout.cancel promise
        promise = null

      promise = $timeout -> elem.addClass 'slow-validate-show'

  require: '^form'
  restrict: 'A'
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


thread = ->
  link: (scope, iElement, iAttrs, controller) ->
    scope.collapsed = false
  restrict: 'C'
  scope: true


userPicker = ->
  restrict: 'ACE'
  scope:
    model: '=userPickerModel'
    options: '=userPickerOptions'
  templateUrl: 'userPicker.html'


#Directive will be removed once the angularjs official version will have this directive
ngBlur = ['$parse', ($parse) ->
  (scope, element, attr) ->
    fn = $parse attr['ngBlur']
    element.bind 'blur', (event) ->
      scope.$apply ->
        fn scope,
          $event: event
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

# Directive to edit/display a word list. Used for tags.
wordlist = ['$filter', '$timeout', '$window', ($filter, $timeout, $window) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    input = elem.find('.wl-editor input')
    output = elem.find('.wl-displayer input')

    # Updates a tag-it widget with the requested viewValue
    update_widget = (widget, field) ->
      if widget?
        # Check whether the current content of the editor
        # is in sync with the actual model value        
        current = widget.assignedTags()
        wanted = ctrl.$viewValue or []
        if (current + '') is (wanted + '')
          # We are good to go, nothing to do
        else      
          # Editor widget's content is different.
          # (Probably because of a cancelled edit.)
          # Copy the tags to the tag editor
          widget.removeAll()
          for tag in wanted
            widget.createTag tag
      else
        # We don't have the widget, so we can simply push value
        # to input box; the widget will fetch it from there
        field.attr 'value', (ctrl.$viewValue or []).join ","

    widgets = {}            

    # Re-render the word list when the view needs updating.
    ctrl.$render = ->
      # Update the editor widget
      update_widget widgets.editor, input

      # update the displayer widget
      update_widget widgets.displayer, output

    # React to the changes in the tag editor
    tagsChanged = -> ctrl.$setViewValue input.val().split ","

    # Re-render when it becomes uneditable.
    scope.$watch 'readonly', (readonly) ->
      if readonly
        unless widgets.displayer?
          # Create displayer widget
          output.attr 'value', (ctrl.$viewValue or []).join ","        
          output.tagit
            readOnly: true
            onTagClicked: (evt, ui) ->
              tag = ui.tagLabel
              $window.open "/t/" + tag
          widgets.displayer = output.data "uiTagit"
      else
        unless widgets.editor?
          # Create editor widget
          console.log "Creating editor"
          input.attr 'value', (ctrl.$viewValue or []).join ","
          input.tagit
            caseSensitive: false
            placeholderText: scope.placeholder
            keepPlaceholder: true
            afterTagAdded: (evt, ui) ->
              if ui.duringInitialization then return
              newTab = ui.tagLabel
              # Create a normalized form
              normalized = newTab.toLowerCase().replace /[^a-z0-9\-\s]/g, ''
              if newTab is normalized
                tagsChanged()
              else
                widgets.editor.removeTagByLabel newTab, false
                widgets.editor.createTag normalized
                
            afterTagRemoved: tagsChanged
            autocomplete:
              source: []
          widgets.editor = input.data "uiTagit"
        
      ctrl.$render()

  require: '?ngModel'
  restrict: 'E'
  scope:
    readonly: '@'
    placeholder: '@'
  templateUrl: '/assets/templates/wordlist.html'
]

angular.module('h.directives', ['ngSanitize'])
  .directive('authentication', authentication)
  .directive('markdown', markdown)
  .directive('privacy', privacy)
  .directive('recursive', recursive)
  .directive('resettable', resettable)
  .directive('slowValidate', slowValidate)
  .directive('tabReveal', tabReveal)
  .directive('thread', thread)
  .directive('userPicker', userPicker)
  .directive('ngBlur', ngBlur)
  .directive('repeatAnim', repeatAnim)
  .directive('wordlist', wordlist)

