loadMathJax = ->
  if !MathJax?
    $.ajax {
      url: "//cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS_HTML-full"
      dataType: 'script'
      cache: true
      complete: ->
        # MathJax configuration overides.
        MathJax.Hub.Config({
          showMathMenu: false
        })
    }

###*
# @ngdoc directive
# @name markdown
# @restrict A
# @description
# This directive controls both the rendering and display of markdown, as well as
# the markdown editor.
###

markdown = ['$filter', '$sanitize', '$sce', '$timeout', ($filter, $sanitize, $sce, $timeout) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    inputEl = elem.find('.js-markdown-input')
    input = elem.find('.js-markdown-input')[0]
    output = elem.find('.js-markdown-preview')[0]

    userSelection = ->
      if input.selectionStart != undefined
        startPos = input.selectionStart
        endPos = input.selectionEnd
        selectedText = input.value.substring(startPos, endPos)
        textBefore = input.value.substring(0, (startPos))
        textAfter = input.value.substring(endPos)
        selection = {
          before: textBefore
          after: textAfter
          selection: selectedText
          start: startPos
          end: endPos
        }
      return selection

    insertMarkup = (value, selectionStart, selectionEnd) ->
      # New value is set for the input
      input.value = value
      # A new selection is set, or the cursor is positioned inside the input.
      input.selectionStart = selectionStart
      input.selectionEnd = selectionEnd
      # Focus the input
      input.focus()

    applyInlineMarkup = (markup, innertext)->
      text = userSelection()
      if text.selection == ""
        newtext = text.before + markup + innertext + markup + text.after
        start = (text.before + markup).length
        end = (text.before + innertext + markup).length
        insertMarkup(newtext, start, end)
      else
        # Check to see if markup has already been applied before to the selection.
        slice1 = text.before.slice(text.before.length - markup.length)
        slice2 = text.after.slice(0, markup.length)
        if slice1 == markup and slice2 == markup
          # Remove markup 
          newtext = (
            text.before.slice(0, (text.before.length - markup.length)) +
            text.selection + text.after.slice(markup.length)
          )
          start = text.before.length - markup.length
          end = (text.before + text.selection).length - markup.length
          insertMarkup(newtext, start, end)
        else
          # Apply markup
          newtext = text.before + markup + text.selection + markup + text.after
          start = (text.before + markup).length
          end = (text.before + text.selection + markup).length
          insertMarkup(newtext, start, end)

    scope.insertBold = ->
      applyInlineMarkup("**", "Bold")

    scope.insertItalic = ->
      applyInlineMarkup("*", "Italic")

    inlineMath = (text) ->
      slice1 = text.before.slice(text.before.length - 2)
      slice2 = text.after.slice(0, 2)
      if slice1 == "\\(" or slice1 == "$$" 
        if slice2 == "\\)" or slice2 == "$$"
          # Remove markup 
          newtext = (
            text.before.slice(0, (text.before.length - 2)) +
            text.selection + text.after.slice(2)
          )
          start = text.before.length - 2
          end = (text.before + text.selection).length - 2
          insertMarkup(newtext, start, end)
          return
      newtext = text.before + "\\(" + "LaTex or MathML" + "\\)" + text.after
      start = text.before.length + 2
      end = (text.before + "LaTex or MathML").length + 2
      insertMarkup(newtext, start, end)

    scope.insertMath = ->
      text = userSelection()
      index = text.before.length
      if index == 0
        # The selection takes place at the very start of the input
        applyInlineMarkup("$$", "LaTex or MathML")
      else if text.selection != ""
        if input.value.substring(index - 1).charAt(0) == "\n"
          # Look to see if the selection falls at the beginning of a new line.
          applyInlineMarkup("$$", "LaTex or MathML")
        else
          inlineMath(text)
      else if input.value.substring((text.start - 1 ), text.start) == "\n"
        # Edge case, no selection, the cursor is on a new line.
        applyInlineMarkup("$$", "LaTex or MathML")
      else
        # No selection, cursor is not on new line.
        inlineMath(text)

    scope.insertLink = ->
      text = userSelection()
      if text.selection == ""
        newtext = text.before + "[Link Text](https://example.com)" + text.after
        start = text.before.length + 1
        end = text.before.length + 10
        insertMarkup(newtext, start, end)
      else
        # Check to see if markup has already been applied to avoid double presses.
        if text.selection == "Link Text" or text.selection == "https://example.com"
          return          
        newtext = text.before + '[' + text.selection + '](https://example.com)' + text.after
        start = (text.before + text.selection).length + 3
        end = (text.before + text.selection).length + 22
        insertMarkup(newtext, start, end)

    scope.insertIMG = ->
      text = userSelection()
      if text.selection == ""
        newtext = text.before + "![Image Description](https://yourimage.jpg)" + text.after
        start = text.before.length + 21
        end = text.before.length + 42
        insertMarkup(newtext, start, end)
      else
        # Check to see if markup has already been applied to avoid double presses.
        if text.selection == "https://yourimage.jpg"
          return     
        newtext = text.before + '![' + text.selection + '](https://yourimage.jpg)' + text.after
        start = (text.before + text.selection).length + 4
        end = (text.before + text.selection).length + 25
        insertMarkup(newtext, start, end)

    scope.applyBlockMarkup = (markup) ->
      text = userSelection()
      if text.selection != ""
        newstring = ""
        index = text.before.length
        if index == 0
          # The selection takes place at the very start of the input
          for char in text.selection
            if char == "\n"
              newstring = newstring + "\n" + markup
            else if index == 0
              newstring = newstring + markup + char
            else
              newstring = newstring + char
            index += 1
        else
          newlinedetected = false
          if input.value.substring(index - 1).charAt(0) == "\n"
            # Look to see if the selection falls at the beginning of a new line.
            newstring = newstring + markup
            newlinedetected = true
          for char in text.selection
            if char == "\n"
              newstring = newstring + "\n" + markup
              newlinedetected = true
            else
              newstring = newstring + char
            index += 1
          if not newlinedetected
            # Edge case: The selection does not include any new lines and does not start at 0.
            # We need to find the newline before the currently selected text and add markup there.
            i = 0
            indexoflastnewline = undefined
            newstring = ""
            for char in (text.before + text.selection)
              if char == "\n"
                indexoflastnewline = i
              newstring = newstring + char
              i++
            if indexoflastnewline == undefined
              # The partial selection happens to fall on the firstline
              newstring = markup + newstring
            else
              newstring = (
                newstring.substring(0, (indexoflastnewline + 1)) +
                markup + newstring.substring(indexoflastnewline + 1)
              )
            value = newstring + text.after
            start = (text.before + markup).length
            end = (text.before + text.selection + markup).length
            insertMarkup(value, start, end)
            return
        # Sets input value and selection for cases where there are new lines in the selection 
        # or the selection is at the start
        value = text.before + newstring + text.after
        start = (text.before + newstring).length
        end = (text.before + newstring).length
        insertMarkup(value, start, end)
      else if input.value.substring((text.start - 1 ), text.start) == "\n"
        # Edge case, no selection, the cursor is on a new line.
        value = text.before + markup + text.selection + text.after
        start = (text.before + markup).length
        end = (text.before + markup).length
        insertMarkup(value, start, end)
      else
        # No selection, cursor is not on new line.
        # Check to see if markup has already been inserted.
        if text.before.slice(text.before.length - markup.length) == markup
          newtext = (
            text.before.substring(0, (index)) + "\n" +
            text.before.substring(index + 1 + markup.length) + text.after
          )
        i = 0
        for char in text.before
          if char == "\n" and i != 0
            index = i
          i += 1
        if !index # If the line of text happens to fall on the first line and index is not set.
          # Check to see if markup has already been inserted and undo it. 
          if text.before.slice(0, markup.length) == markup
            newtext = text.before.substring(markup.length) + text.after
            start = text.before.length - markup.length
            end = text.before.length - markup.length
            insertMarkup(newtext, start, end)
          else
            newtext = markup + text.before.substring(0) + text.after
            start = (text.before + markup).length
            end = (text.before + markup).length
            insertMarkup(newtext, start, end)
        # Check to see if markup has already been inserted and undo it.
        else if text.before.slice((index + 1), (index + 1 + markup.length)) == markup
          newtext = (
            text.before.substring(0, (index)) + "\n" +
            text.before.substring(index + 1 + markup.length) + text.after
          )
          start = text.before.length - markup.length
          end = text.before.length - markup.length
          insertMarkup(newtext, start, end)
        else
          newtext = (
            text.before.substring(0, (index)) + "\n" +
            markup + text.before.substring(index + 1) + text.after
          )
          start = (text.before + markup).length
          end = (text.before + markup).length
          insertMarkup(newtext, start, end)

    scope.insertList = ->
      scope.applyBlockMarkup("* ")

    scope.insertNumList = ->
      scope.applyBlockMarkup("1. ")

    scope.insertQuote = ->
      scope.applyBlockMarkup("> ")
      
    scope.insertCode = ->
      scope.applyBlockMarkup("    ")

    # Keyboard shortcuts for bold, italic, and link.
    elem.on
      keydown: (e) ->
        shortcuts =
          66: scope.insertBold
          73: scope.insertItalic
          75: scope.insertLink

        shortcut = shortcuts[e.keyCode]
        if shortcut && (e.ctrlKey || e.metaKey)
          e.preventDefault()
          shortcut()

    scope.preview = false
    scope.togglePreview = ->
      if !scope.readonly
        scope.preview = !scope.preview
        if scope.preview
          output.style.height = input.style.height
          ctrl.$render()
        else
          input.style.height = output.style.height
          $timeout -> inputEl.focus()

    MathJaxFallback = false
    # Re-render the markdown when the view needs updating.
    ctrl.$render = ->
      if !scope.readonly and !scope.preview
        inputEl.val (ctrl.$viewValue or '')
      value = ctrl.$viewValue or ''
      convert = $filter('converter')
      re = /(?:\$\$)|(?:\\\(|\\\))/g

      startMath = 0
      endMath = 0
      i = 0
      parts = []

      indexes = (match while match = re.exec(value))
      indexes.push(value.length)

      for match in indexes
        if startMath > endMath
          endMath = match.index + 2
          try
            parts.push katex.renderToString($sanitize value.substring(startMath, match.index))
          catch
            loadMathJax()
            MathJaxFallback = true
            parts.push $sanitize value.substring(startMath, match.index)
        else
          startMath = match.index + 2
          # Inline math needs to fall inline, which can be tricky considering the markdown
          # converter will take the part that comes before a peice of math and surround it
          # with markup: <p>Here is some inline math: </p>\(2 + 2 = 4\)
          # Here we look for various cases.
          if match[0] == "\\("
            # Text falls between two instances of inline math, we must remove the opening and
            # closing <p> tags since this is meant to be one paragraph.
            if i - 1 >= 0 and indexes[i - 1].toString() == "\\)"
              markdown = $sanitize convert value.substring(endMath, match.index)
              parts.push markdown.substring(3, markdown.length - 4)
            # Text preceeds a case of inline math. We must remove the ending </p> tag
            # so that the math is inline.
            else
              markdown = $sanitize convert value.substring(endMath, match.index)
              parts.push markdown.substring(0, markdown.length - 4)
          # Text follows a case of inline math, we must remove opening <p> tag.
          else if i - 1 >= 0 and indexes[i - 1].toString() == "\\)"
            markdown = $sanitize convert value.substring(endMath, match.index)
            parts.push markdown.substring(3, markdown.length)
          else # Block Math or no math.
            parts.push $sanitize convert value.substring(endMath, match.index)
        i++
      scope.rendered = $sce.trustAsHtml parts.join('')
      if MathJaxFallback
        $timeout (-> MathJax?.Hub.Queue ['Typeset', MathJax.Hub, output]), 0, false

    # React to the changes to the input
    inputEl.bind 'blur change keyup', ->
      ctrl.$setViewValue inputEl.val()
      scope.$digest()

    # Reset height of output div incase it has been changed.
    # Re-render when it becomes uneditable.
    # Auto-focus the input box when the widget becomes editable.
    scope.$watch 'readonly', (readonly) ->
      scope.preview = false
      output.style.height = ""
      ctrl.$render()
      unless readonly then $timeout -> inputEl.focus()

  require: '?ngModel'
  restrict: 'A'
  scope:
    readonly: '@'
    required: '@'
  templateUrl: 'markdown.html'
]

angular.module('h')
.directive('markdown', markdown)
