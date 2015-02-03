assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Guest', ->
  sandbox = sinon.sandbox.create()
  fakeCFBridge = null
  createGuest = (options) ->
    element = document.createElement('div')
    return new Annotator.Guest(element, options || {})

  # Silence Annotator's sassy backchat
  beforeEach -> sandbox.stub(console, 'log')
  afterEach -> sandbox.restore()

  describe 'setting up the bridge', ->
    beforeEach ->
      fakeCFBridge =
        onConnect: sandbox.stub()
        on: sandbox.stub()

      sinon.stub(Annotator.Plugin, 'Bridge').returns
        bridge: fakeCFBridge

    it 'sets the scope for the cross frame bridge', ->
      guest = createGuest()
      options = Annotator.Plugin.Bridge.lastCall.args[1]
      assert.equal(options.bridgeOptions.scope, 'annotator:bridge')

    it 'provides an event bus for the annotation sync module'
    it 'provides a formatter for the annotation sync module'
    it 'publishes the "panelReady event when a connection is established'

    describe 'the event bus .on method', ->
      it 'proxies the event into the annotator event system'

    describe 'the event bus .emit method', ->
      it 'calls deleteAnnotations when an annotationDeleted event is recieved'
      it 'does not proxy the deleteAnnotations event'
      it 'calls loadAnnotations when an loadAnnotations event is recieved'
      it 'does not proxy the loadAnnotations event'
      it 'proxies all other events into the annotator event system'

    describe 'the formatter', ->
      it 'applies a "uri" property to the formatted object'
      it 'copies the properties from the provided annotation'
      it 'strips the "anchors" property'
      it 'clones the document.title array if present'

  describe 'annotation UI events', ->
    describe 'on "onEditorHide" event', ->
      it 'hides the editor'
    describe 'on "onEditorSubmit" event', ->
      it 'sumbits the editor'
    describe 'on "focusAnnotations" event', ->
      it 'focuses any annotations with a matching tag'
      it 'unfocuses any annotations without a matching tag'
    describe 'on "scrollToAnnotation" event', ->
      it 'scrolls to the highlight with the matching tag'
    describe 'on "getDocumentInfo" event', ->
      it 'calls the callback with the href and pdf metadata'
      it 'calls the callback with the href and document metadata if pdf check fails'
      it 'notifies the channel that the return value is async'
    describe 'on "setTool" event', ->
      it 'updates the .tool property'
      it 'publishes the "setTool" event'
    describe 'on "setVisibleHighlights" event', ->
      it 'publishes the "setVisibleHighlights" event'

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
