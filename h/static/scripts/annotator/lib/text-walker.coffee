###*
# The `text-walker` module provides a single class, `TextWalker`, and
# assocatied constants for seeking within the text content of a `Node` tree.
###
SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2

# A NodeFilter bitmask that matches node types included by `Node.textContent`.
TEXT_CONTENT_FILTER = (
  NodeFilter.SHOW_ALL &
  ~NodeFilter.SHOW_COMMENT &
  ~NodeFilter.SHOW_PROCESSING_INSTRUCTION
)


class TextWalker
  constructor: (root, filter) ->
    @root = root
    @currentNode = root
    @filter = filter
    @offset = 0

  ###*
  # Seek the `TextWalker` to a new text offset.
  #
  # The value of `whence` determines the meaning of `offset`. It may be one
  # of `SEEK_SET`, `SEEK_CUR` or `SEEK_END`. The meaning is the same as for
  # POSIX lseek(2) except that it is impossible to seek past the end of the
  # text.
  ###
  seek: (offset, whence) ->
    walker = document.createTreeWalker(@root, TEXT_CONTENT_FILTER, @filter)

    switch whence
      when SEEK_SET
        @offset = 0
        walker.currentNode = @root
      when SEEK_CUR
        # XXX: Only two hard problems...
        walker.currentNode = @currentNode
      when SEEK_END
        throw new Error('Seeking from the end not yet supported')

    # Walk forwards
    while offset > 0
      step = walker.currentNode.textContent.length

      # If this node is longer than the remainder to seek then step in to it.
      if step > offset

        # If there is no smaller step to take then finish.
        if walker.firstChild() is null
          break

        # Otherwise, continue with the first child.
        else
          continue

      # If this node is not longer than the seek then try to step over it.
      else if walker.nextSibling() is null

        # Failing that, step out or finish.
        if walker.nextNode() is null
          break

      # Update the instance offset cache
      @offset += step

      # Decrease the remainder offset and continue.
      offset -= step

    # Walk backwards
    while offset < 0
      throw new Error('Negative offset values not yet supported.')

    # Store the current node
    @currentNode = walker.currentNode

    # Return the offset.
    return @offset

  tell: ->
    # Calculating the offset is the safest way to be correct even if the DOM
    # has changed since this instance was created, but it is obviously slow.
    offset = 0
    walker = document.createTreeWalker(@root, TEXT_CONTENT_FILTER, @filter)

    # Start from the current node.
    walker.currentNode = @currentNode

    # Continue until reaching the root.
    while walker.currentNode isnt walker.root

      # Step backwards through siblings, to count the leading content.
      while node = walker.previousSibling()
        offset += node.textContent.length

      # Step up to the parent and continue until done.
      walker.parentNode()

    # Store and return the offset.
    @offset = offset
    return @offset

exports.SEEK_SET = SEEK_SET
exports.SEEK_CUR = SEEK_CUR
exports.SEEK_END = SEEK_END
exports.TextWalker = TextWalker
