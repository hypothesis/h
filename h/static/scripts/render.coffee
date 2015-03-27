###*
# @ngdoc service
# @name render
# @param {function()} fn A function to execute in a future animation frame.
# @returns {function()} A function to cancel the execution.
# @description
# The render service is a wrapper around `window#requestAnimationFrame()` for
# scheduling sequential updates in successive animation frames. It has the
# same signature as the original function, but will queue successive calls
# for future frames so that at most one callback is handled per animation frame.
# Use this service to schedule DOM-intensive digests.
###
module.exports = ['$$rAF', ($$rAF) ->
  cancel = null
  queue = []

  render = ->
    return cancel = null if queue.length is 0
    do queue.shift()
    $$rAF(render)

  (fn) ->
    queue.push fn
    unless cancel then cancel = $$rAF(render)
    -> queue = (f for f in queue when f isnt fn)
]
