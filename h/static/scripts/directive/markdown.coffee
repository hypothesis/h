mediaEmbedder = require('../media-embedder')

loadMathJax = ->
  if !MathJax?
    $.ajax {
      url: "https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS_HTML-full"
      dataType: 'script'
      cache: true
      complete: ->
        # MathJax configuration overides.
        MathJax.Hub.Config({
          showMathMenu: false
          displayAlign: "left"
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

module.exports = ['$filter', '$sanitize', '$sce', '$timeout', ($filter, $sanitize, $sce, $timeout) ->
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

    applyInlineMarkup = (markupL, innertext, markupR) ->
      markupR or= markupL
      text = userSelection()
      if text.selection == ""
        newtext = text.before + markupL + innertext + markupR + text.after
        start = (text.before + markupL).length
        end = (text.before + innertext + markupR).length
        insertMarkup(newtext, start, end)
      else
        # Check to see if markup has already been applied before to the selection.
        slice1 = text.before.slice(text.before.length - markupL.length)
        slice2 = text.after.slice(0, markupR.length)
        if (slice1 == markupL and slice2 == markupR)
          # Remove markup
          newtext = (
            text.before.slice(0, (text.before.length - markupL.length)) +
            text.selection + text.after.slice(markupR.length)
          )
          start = text.before.length - markupL.length
          end = (text.before + text.selection).length - markupR.length
          insertMarkup(newtext, start, end)
        else
          # Apply markup
          newtext = text.before + markupL + text.selection + markupR + text.after
          start = (text.before + markupL).length
          end = (text.before + text.selection + markupR).length
          insertMarkup(newtext, start, end)

    scope.insertBold = ->
      applyInlineMarkup("**", "Bold")

    scope.insertItalic = ->
      applyInlineMarkup("*", "Italic")

    scope.insertMath = ->
      text = userSelection()
      index = text.before.length
      if (
        index == 0 or
        input.value[index - 1] == '\n' or
        (input.value[index - 1] == '$' and input.value[index - 2] == '$')
      )
        applyInlineMarkup('$$', 'Insert LaTeX')
      else
        applyInlineMarkup('\\(', 'Insert LaTeX', '\\)')

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
      if !scope.readOnly
        scope.preview = !scope.preview
        if scope.preview
          output.style.height = input.style.height
          ctrl.$render()
        else
          input.style.height = output.style.height
          $timeout -> inputEl.focus()

    mathJaxFallback = false
    renderMathAndMarkdown = (textToCheck) ->
      convert = $filter('converter')
      re = /\$\$/g

      startMath = 0
      endMath = 0

      indexes = (match.index while match = re.exec(textToCheck))
      indexes.push(textToCheck.length)

      parts = for index in indexes
        if startMath > endMath
          endMath = index + 2
          try
            # \\displaystyle tells KaTeX to render the math in display style (full sized fonts).
            katex.renderToString($sanitize "\\displaystyle {" + textToCheck.substring(startMath, index) + "}")
          catch
            loadMathJax()
            mathJaxFallback = true
            $sanitize textToCheck.substring(startMath, index)
        else
          startMath = index + 2
          $sanitize convert renderInlineMath textToCheck.substring(endMath, index)

      htmlString = parts.join('')

      # Transform the HTML string into a DOM element.
      domElement = document.createElement('div')
      domElement.innerHTML = htmlString

      mediaEmbedder.replaceLinksWithEmbeds(domElement)

      return domElement.innerHTML

    renderInlineMath = (textToCheck) ->
      re = /\\?\\\(|\\?\\\)/g
      startMath = null
      endMath = null
      match = undefined
      indexes = []
      while match = re.exec(textToCheck)
        indexes.push match.index
      for index in indexes
        if startMath == null
          startMath = index + 2
        else
          endMath = index
        if startMath != null and endMath != null
          try
            math = katex.renderToString(textToCheck.substring(startMath, endMath))
            textToCheck = (
              textToCheck.substring(0, (startMath - 2)) + math +
              textToCheck.substring(endMath + 2)
            )
            startMath = null
            endMath = null
            return renderInlineMath(textToCheck)
          catch
            loadMathJax()
            mathJaxFallback = true
            $sanitize textToCheck.substring(startMath, endMath)
      return textToCheck

    # Re-render the markdown when the view needs updating.
    ctrl.$render = ->
      if !scope.readOnly and !scope.preview
        inputEl.val (ctrl.$viewValue or '')
      value = ctrl.$viewValue or ''
      output.innerHTML = renderMathAndMarkdown(value)
      if mathJaxFallback
        $timeout (-> MathJax?.Hub.Queue ['Typeset', MathJax.Hub, output]), 0, false

    # React to the changes to the input
    inputEl.bind 'blur change keyup', ->
      $timeout -> ctrl.$setViewValue inputEl.val()

    # Reset height of output div incase it has been changed.
    # Re-render when it becomes uneditable.
    # Auto-focus the input box when the widget becomes editable.
    scope.$watch 'readOnly', (readOnly) ->
      scope.preview = false
      output.style.height = ""
      ctrl.$render()
      unless readOnly then $timeout -> inputEl.focus()

  require: '?ngModel'
  restrict: 'E'
  scope:
    readOnly: '='
    required: '@'
  templateUrl: 'markdown.html'
]
