module.exports = ->
  _drafts = []

  all: -> draft for {draft} in _drafts

  add: (draft, cb) -> _drafts.push {draft, cb}

  remove: (draft) ->
    remove = []
    for d, i in _drafts
      remove.push i if d.draft is draft
    while remove.length
      _drafts.splice(remove.pop(), 1)

  contains: (draft) ->
    for d in _drafts
      if d.draft is draft then return true
    return false

  isEmpty: -> _drafts.length is 0

  discard: ->
    text =
      switch _drafts.length
        when 0 then null
        when 1
          """You have an unsaved reply.

          Do you really want to discard this draft?"""
        else
          """You have #{_drafts.length} unsaved replies.

          Do you really want to discard these drafts?"""

    if _drafts.length is 0 or confirm text
      discarded = _drafts.slice()
      _drafts = []
      d.cb?() for d in discarded
      true
    else
      false
