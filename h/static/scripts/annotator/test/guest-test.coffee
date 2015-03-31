Promise = require('es6-promise').Promise
Annotator = require('annotator')
Guest = require('../guest')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


describe 'Guest', ->
  sandbox = null
  fakeCrossFrame = null

  createGuest = (options) ->
    element = document.createElement('div')
    return new Guest(element, options || {})

  beforeEach ->
    sandbox = sinon.sandbox.create()

    fakeCrossFrame =
      onConnect: sandbox.stub()
      on: sandbox.stub()
      sync: sandbox.stub()

    Annotator.Plugin.CrossFrame = -> fakeCrossFrame
    sandbox.spy(Annotator.Plugin, 'CrossFrame')

  afterEach ->
    sandbox.restore()

  describe 'setting up the bridge', ->

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

      it 'calls deleteAnnotation when an annotationDeleted event is received', ->
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

      it 'calls loadAnnotations when an loadAnnotations event is received', ->
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
        target = sandbox.stub(Guest.prototype, 'onEditorHide')
        guest = createGuest()
        emitGuestEvent('onEditorHide')
        assert.called(target)

    describe 'on "onEditorSubmit" event', ->
      it 'sumbits the editor', ->
        target = sandbox.stub(Guest.prototype, 'onEditorSubmit')
        guest = createGuest()
        emitGuestEvent('onEditorSubmit')
        assert.called(target)

    describe 'on "focusAnnotations" event', ->
      it 'focuses any annotations with a matching tag', ->
        highlight0 = {setFocused: sandbox.stub()}
        highlight1 = {setFocused: sandbox.stub()}
        guest = createGuest()
        guest.anchored = [
          {annotation: {$$tag: 'tag1'}, highlight: highlight0}
          {annotation: {$$tag: 'tag2'}, highlight: highlight1}
        ]
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.called(highlight0.setFocused)
        assert.calledWith(highlight0.setFocused, true)

      it 'unfocuses any annotations without a matching tag', ->
        highlight0 = {setFocused: sandbox.stub()}
        highlight1 = {setFocused: sandbox.stub()}
        guest = createGuest()
        guest.anchored = [
          {annotation: {$$tag: 'tag1'}, highlight: highlight0}
          {annotation: {$$tag: 'tag2'}, highlight: highlight1}
        ]
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.called(highlight1.setFocused)
        assert.calledWith(highlight1.setFocused, false)

    describe 'on "scrollToAnnotation" event', ->
      it 'scrolls to the anchor with the matching tag', ->
        highlight = {scrollToView: sandbox.stub()}
        guest = createGuest()
        guest.anchored = [
          {annotation: {$$tag: 'tag1'}, highlight: highlight}
        ]
        emitGuestEvent('scrollToAnnotation', 'ctx', 'tag1')
        assert.called(highlight.scrollToView)

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

  describe 'annotation sync', ->
    it 'calls sync for createAnnotation', ->
      guest = createGuest()
      guest.createAnnotation({})
      assert.called(fakeCrossFrame.sync)

    it 'calls sync for setupAnnotation', (done) ->
      guest = createGuest()
      guest.plugins.Document = {uri: -> 'http://example.com'}
      guest.setupAnnotation({})
      setTimeout ->
        assert.called(fakeCrossFrame.sync)
        done()

  describe 'setupAnnotation()', ->
    it "doesn't declare annotation without targets as orphans", (done) ->
      guest = createGuest()
      annotation = target: []
      guest.setupAnnotation(annotation)
      setTimeout ->
        assert.isFalse !!annotation.$orphan
        done()

    it "doesn't declare annotations with a working target as orphans", (done) ->
      guest = createGuest()
      annotation = target: ["test target"]
      guest.setupAnnotation(annotation)
      setTimeout ->
        assert.isFalse !!annotation.$orphan
        done()

    it "declares annotations with broken targets as orphans", (done) ->
      guest = createGuest()
      sandbox.stub(guest, 'anchorTarget').returns(Promise.reject())
      annotation = target: [{selector: 'broken selector'}]
      guest.setupAnnotation(annotation)
      setTimeout ->
        assert !!annotation.$orphan
        done()
