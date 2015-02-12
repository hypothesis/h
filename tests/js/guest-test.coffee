assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Guest', ->
  sandbox = sinon.sandbox.create()
  fakeCrossFrame = null
  createGuest = (options) ->
    element = document.createElement('div')
    return new Annotator.Guest(element, options || {})

  # Silence Annotator's sassy backchat
  beforeEach -> sandbox.stub(console, 'log')
  afterEach -> sandbox.restore()

  beforeEach ->
    fakeCrossFrame =
      onConnect: sandbox.stub()
      on: sandbox.stub()

    sandbox.stub(Annotator.Plugin, 'CrossFrame').returns(fakeCrossFrame)

  describe 'setting up the bridge', ->
    it 'sets the scope for the cross frame bridge', ->
      guest = createGuest()
      options = Annotator.Plugin.CrossFrame.lastCall.args[1]
      assert.equal(options.scope, 'annotator:bridge')

    it 'provides an event bus for the annotation sync module', ->
      guest = createGuest()
      options = Annotator.Plugin.CrossFrame.lastCall.args[1]
      assert.isFunction(options.on)
      assert.isFunction(options.emit)

    it 'provides a formatter for the annotation sync module', ->
      guest = createGuest()
      options = Annotator.Plugin.CrossFrame.lastCall.args[1]
      assert.isFunction(options.formatter)

    it 'publishes the "panelReady" event when a connection is established', ->
      handler = sandbox.stub()
      guest = createGuest()
      guest.subscribe('panelReady', handler)
      fakeCrossFrame.onConnect.yield()
      assert.called(handler)

    describe 'the event bus .on method', ->
      options = null
      guest = null

      beforeEach ->
        guest = createGuest()
        options = Annotator.Plugin.CrossFrame.lastCall.args[1]

      it 'proxies the event into the annotator event system', ->
        fooHandler = sandbox.stub()
        barHandler = sandbox.stub()

        options.on('foo', fooHandler)
        options.on('bar', barHandler)

        guest.publish('foo', ['1', '2'])
        guest.publish('bar', ['1', '2'])

        assert.calledWith(fooHandler, '1', '2')
        assert.calledWith(barHandler, '1', '2')

    describe 'the event bus .emit method', ->
      options = null
      guest = null

      beforeEach ->
        guest = createGuest()
        options = Annotator.Plugin.CrossFrame.lastCall.args[1]

      it 'calls deleteAnnotation when an annotationDeleted event is recieved', ->
        ann = {id: 1, $$tag: 'tag1'}
        sandbox.stub(guest, 'deleteAnnotation')

        options.emit('annotationDeleted', ann)
        assert.called(guest.deleteAnnotation)
        assert.calledWith(guest.deleteAnnotation, ann)

      it 'does not proxy the annotationDeleted event', ->
        handler = sandbox.stub()
        guest.subscribe('annotationDeleted', handler)

        options.emit('annotationDeleted', {})
        # Called only once by the deleteAnnotation() method.
        assert.calledOnce(handler)

      it 'calls loadAnnotations when an loadAnnotations event is recieved', ->
        ann = {id: 1, $$tag: 'tag1'}
        target = sandbox.stub(guest, 'loadAnnotations')

        options.emit('loadAnnotations', [ann])
        assert.called(target)
        assert.calledWith(target, [ann])

      it 'does not proxy the loadAnnotations event', ->
        handler = sandbox.stub()
        guest.subscribe('loadAnnotations', handler)

        options.emit('loadAnnotations', [])
        assert.notCalled(handler)

      it 'proxies all other events into the annotator event system', ->
        fooHandler = sandbox.stub()
        barHandler = sandbox.stub()

        guest.subscribe('foo', fooHandler)
        guest.subscribe('bar', barHandler)

        options.emit('foo', '1', '2')
        options.emit('bar', '1', '2')

        assert.calledWith(fooHandler, '1', '2')
        assert.calledWith(barHandler, '1', '2')

    describe 'the formatter', ->
      options = null
      guest = null

      beforeEach ->
        guest = createGuest()
        guest.plugins.Document = {uri: -> 'http://example.com'}
        options = Annotator.Plugin.CrossFrame.lastCall.args[1]

      it 'applies a "uri" property to the formatted object', ->
        ann = {$$tag: 'tag1'}
        formatted = options.formatter(ann)
        assert.equal(formatted.uri, 'http://example.com/')

      it 'keeps an existing uri property', ->
        ann = {$$tag: 'tag1', uri: 'http://example.com/foo'}
        formatted = options.formatter(ann)
        assert.equal(formatted.uri, 'http://example.com/foo')

      it 'copies the properties from the provided annotation', ->
        ann = {$$tag: 'tag1'}
        formatted = options.formatter(ann)
        assert.equal(formatted.$$tag, 'tag1')

      it 'strips the "anchors" property', ->
        ann = {$$tag: 'tag1', anchors: []}
        formatted = options.formatter(ann)
        assert.notProperty(formatted, 'anchors')

      it 'clones the document.title array if present', ->
        title = ['Page Title']
        ann = {$$tag: 'tag1', document: {title: title}}
        formatted = options.formatter(ann)
        assert.notStrictEqual(title, formatted.document.title)
        assert.deepEqual(title, formatted.document.title)

  describe 'annotation UI events', ->
    emitGuestEvent = (event, args...) ->
      fn(args...) for [evt, fn] in fakeCrossFrame.on.args when event == evt

    describe 'on "onEditorHide" event', ->
      it 'hides the editor', ->
        target = sandbox.stub(Annotator.Guest.prototype, 'onEditorHide')
        guest = createGuest()
        emitGuestEvent('onEditorHide')
        assert.called(target)

    describe 'on "onEditorSubmit" event', ->
      it 'sumbits the editor', ->
        target = sandbox.stub(Annotator.Guest.prototype, 'onEditorSubmit')
        guest = createGuest()
        emitGuestEvent('onEditorSubmit')
        assert.called(target)

    describe 'on "focusAnnotations" event', ->
      it 'focuses any annotations with a matching tag', ->
        guest = createGuest()
        highlights = [
          {annotation: {$$tag: 'tag1'}, setFocused: sandbox.stub()}
          {annotation: {$$tag: 'tag2'}, setFocused: sandbox.stub()}
        ]
        sandbox.stub(guest.anchoring, 'getHighlights').returns(highlights)
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.called(highlights[0].setFocused)
        assert.calledWith(highlights[0].setFocused, true)

      it 'unfocuses any annotations without a matching tag', ->
        guest = createGuest()
        highlights = [
          {annotation: {$$tag: 'tag1'}, setFocused: sandbox.stub()}
          {annotation: {$$tag: 'tag2'}, setFocused: sandbox.stub()}
        ]
        sandbox.stub(guest.anchoring, 'getHighlights').returns(highlights)
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.called(highlights[1].setFocused)
        assert.calledWith(highlights[1].setFocused, false)

    describe 'on "scrollToAnnotation" event', ->
      it 'scrolls to the anchor with the matching tag', ->
        guest = createGuest()
        anchors = [
          {annotation: {$$tag: 'tag1'}, scrollIntoView: sandbox.stub()}
        ]
        sandbox.stub(guest.anchoring, 'getAnchors').returns(anchors)
        emitGuestEvent('scrollToAnnotation', 'ctx', 'tag1')
        assert.called(anchors[0].scrollIntoView)

    describe 'on "getDocumentInfo" event', ->
      guest = null

      beforeEach ->
        guest = createGuest()
        guest.plugins.PDF =
          uri: sandbox.stub().returns('http://example.com')
          getMetaData: sandbox.stub()

      it 'calls the callback with the href and pdf metadata', (done) ->
        assertComplete = (payload) ->
          try
            assert.equal(payload.uri, 'http://example.com/')
            assert.equal(payload.metadata, metadata)
            done()
          catch e
            done(e)

        ctx = {complete: assertComplete, delayReturn: sandbox.stub()}
        metadata = {title: 'hi'}
        promise = Promise.resolve(metadata)
        guest.plugins.PDF.getMetaData.returns(promise)

        emitGuestEvent('getDocumentInfo', ctx)

      it 'calls the callback with the href and document metadata if pdf check fails', (done) ->
        assertComplete = (payload) ->
          try
            assert.equal(payload.uri, 'http://example.com/')
            assert.equal(payload.metadata, metadata)
            done()
          catch e
            done(e)

        ctx = {complete: assertComplete, delayReturn: sandbox.stub()}
        metadata = {title: 'hi'}
        guest.plugins.Document = {metadata: metadata}

        promise = Promise.reject(new Error('Not a PDF document'))
        guest.plugins.PDF.getMetaData.returns(promise)

        emitGuestEvent('getDocumentInfo', ctx)
      it 'notifies the channel that the return value is async', ->
        delete guest.plugins.PDF

        ctx = {complete: sandbox.stub(), delayReturn: sandbox.stub()}
        emitGuestEvent('getDocumentInfo', ctx)
        assert.calledWith(ctx.delayReturn, true)

    describe 'on "setTool" event', ->
      it 'updates the .tool property', ->
        guest = createGuest()
        emitGuestEvent('setTool', 'ctx', 'highlighter')
        assert.equal(guest.tool, 'highlighter')

      it 'publishes the "setTool" event', ->
        handler = sandbox.stub()
        guest = createGuest()
        guest.subscribe('setTool', handler)
        emitGuestEvent('setTool', 'ctx', 'highlighter')
        assert.called(handler)
        assert.calledWith(handler, 'highlighter')

    describe 'on "setVisibleHighlights" event', ->
      it 'publishes the "setVisibleHighlights" event', ->
        handler = sandbox.stub()
        guest = createGuest()
        guest.subscribe('setTool', handler)
        emitGuestEvent('setTool', 'ctx', 'highlighter')
        assert.called(handler)
        assert.calledWith(handler, 'highlighter')

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
