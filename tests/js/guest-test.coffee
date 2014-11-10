assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Guest', ->
  createGuest = (options) ->
    element = document.createElement('div')
    return new Annotator.Guest(element, options || {})

  # Silence Annotator's sassy backchat
  before -> sinon.stub(console, 'log')
  after -> console.log.restore()

  describe 'onAdderMouseUp', ->
    it 'it prevents the default browser action when triggered', () ->
      event = jQuery.Event('mouseup')
      guest = createGuest()
      guest.onAdderMouseup(event)
      assert.isTrue(event.isDefaultPrevented())

    it 'it stops any further event bubbling', () ->
      event = jQuery.Event('mouseup')
      guest = createGuest()
      guest.onAdderMouseup(event)
      assert.isTrue(event.isPropagationStopped())
