###*
# @ngdoc directive
# @name markdown
# @restrict A
# @description
# This directive controls both the rendering and display of markdown in annotations, as well as
# the markdown editor.
###

markdown = ['$filter', '$timeout', '$window', ($filter, $timeout, $window) ->
  link: (scope, elem, attr, ctrl) ->
    return unless ctrl?

    input = elem.find('textarea')
    output = elem.find('div')

    returnSelection = ->
      ourIframeSelection = $window.getSelection().toString()
      if input[0].selectionStart != undefined
        startPos = input[0].selectionStart
        endPos = input[0].selectionEnd
        if ourIframeSelection
          selectedText = ourIframeSelection
        else
          selectedText = input[0].value.substring(startPos, endPos)
        textBefore = input[0].value.substring(0, (startPos))
        textAfter = input[0].value.substring(endPos)
        selection = {
          before: textBefore
          after: textAfter
          selection: selectedText
          start: startPos
          end: endPos
        }
      input.focus()
      return selection

    insertMarkup = (value, selectionStart, selectionEnd) ->
      # New value is set for the textarea
      input[0].value = value
      # A new selection is set, or the cursur is positioned inside the textarea.
      input[0].selectionStart = selectionStart
      input[0].selectionEnd = selectionEnd

    applyInlineMarkup = (markup, innertext)->
      text = returnSelection()
      if text.selection == ""
        newtext = text.before + markup + innertext + markup + text.after
        start = (text.before + markup).length
        end = (text.before + innertext + markup).length
        insertMarkup(newtext, start, end)
      else
        # Check to see if markup has already been applied before to the selection.
        slice1 = text.before.slice((text.before.length - markup.length))
        slice2 = text.after.slice(0, markup.length)
        if slice1 == markup and slice2 == markup
          # Remove markup 
          newtext = text.before.slice(0, (text.before.length - markup.length)) + text.selection + text.after.slice(markup.length)
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

    scope.insertMath = ->
      applyInlineMarkup("$$", "LaTex")

    scope.insertLink = ->
      text = returnSelection()
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
      text = returnSelection()
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
      text = returnSelection()
      if text.selection != ""
        newstring = ""
        index = text.before.length
        if index == 0
          # The selection takes place at the very start of the textarea
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
          if input[0].value.substring(index - 1).charAt(0) == "\n"
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
              newstring = newstring.substring(0, (indexoflastnewline + 1)) + markup + newstring.substring(indexoflastnewline + 1)
            value = newstring + text.after
            start = (text.before + markup).length
            end = (text.before + text.selection + markup).length
            insertMarkup(value, start, end)
            return
        # Sets textarea value and selection for cases where there are new lines in the selection 
        # or the selection is at the start
        value = text.before + newstring + text.after
        start = (text.before + newstring).length
        end = (text.before + newstring).length
        insertMarkup(value, start, end)
      else if input[0].value.substring((text.start - 1 ), text.start) == "\n"
        # Edge case, no selection, the cursor is on a new line.
        value = text.before + markup + text.selection + text.after
        start = (text.before + markup).length
        end = (text.before + markup).length
        insertMarkup(value, start, end)
      else
        # No selection, cursor is not on new line. Go to the previous newline and insert markup there.
        # # Check to see if markup has already been inserted.
        if text.before.slice(text.before.length - markup.length) == markup
          newtext = text.before.substring(0, (index)) + "\n" + text.before.substring(index + 1 + markup.length) + text.after
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
          newtext = text.before.substring(0, (index)) + "\n" + text.before.substring(index + 1 + markup.length) + text.after
          start = text.before.length - markup.length
          end = text.before.length - markup.length
          insertMarkup(newtext, start, end)
        else
          newtext = text.before.substring(0, (index)) + "\n" + markup + text.before.substring(index + 1) + text.after
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
          output[2].style.height = input[0].style.height
          ctrl.$render()
        else
          input[0].style.height = output[2].style.height
          $timeout -> input.focus()

    # Re-render the markdown when the view needs updating.
    ctrl.$render = ->
      input.val (ctrl.$viewValue or '')
      scope.rendered = ($filter 'converter') (ctrl.$viewValue or '')

    # React to the changes to the text area
    input.bind 'blur change keyup', ->
      ctrl.$setViewValue input.val()
      scope.$digest()

    # Reset height of output div incase it has been changed.
    # Re-render when it becomes uneditable.
    # Auto-focus the input box when the widget becomes editable.
    scope.$watch 'readonly', (readonly) ->
      scope.preview = false
      output[2].style.height = ""
      ctrl.$render()
      unless readonly then $timeout -> input.focus()

  require: '?ngModel'
  restrict: 'A'
  scope:
    readonly: '@'
    required: '@'
  templateUrl: 'markdown.html'
]

angular.module('h.directives').directive('markdown', markdown)
