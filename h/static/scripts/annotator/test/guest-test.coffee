Promise = global.Promise ? require('es6-promise').Promise
Annotator = require('annotator')
Guest = require('../guest')
anchoring = require('../anchoring/html')
highlighter = require('../highlighter')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


waitForSync = (annotation) ->
  if annotation.$anchors?
    return Promise.resolve()
  else
    return new Promise(setTimeout).then(-> waitForSync(annotation))


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
        options = Annotator.Plugin.CrossFrame.lastCall.args[1]

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
        highlight0 = $('<span></span>')
        highlight1 = $('<span></span>')
        guest = createGuest()
        guest.anchors = [
          {annotation: {$$tag: 'tag1'}, highlights: highlight0.toArray()}
          {annotation: {$$tag: 'tag2'}, highlights: highlight1.toArray()}
        ]
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.isTrue(highlight0.hasClass('annotator-hl-focused'))

      it 'unfocuses any annotations without a matching tag', ->
        highlight0 = $('<span class="annotator-hl-focused"></span>')
        highlight1 = $('<span class="annotator-hl-focused"></span>')
        guest = createGuest()
        guest.anchors = [
          {annotation: {$$tag: 'tag1'}, highlights: highlight0.toArray()}
          {annotation: {$$tag: 'tag2'}, highlights: highlight1.toArray()}
        ]
        emitGuestEvent('focusAnnotations', 'ctx', ['tag1'])
        assert.isFalse(highlight1.hasClass('annotator-hl-focused'))

    describe 'on "scrollToAnnotation" event', ->
      beforeEach ->
        $.fn.scrollintoview = sandbox.stub()

      afterEach ->
        delete $.fn.scrollintoview

      it 'scrolls to the anchor with the matching tag', ->
        highlight = $('<span></span>')
        guest = createGuest()
        guest.anchors = [
          {annotation: {$$tag: 'tag1'}, highlights: highlight.toArray()}
        ]
        emitGuestEvent('scrollToAnnotation', 'ctx', 'tag1')
        assert.calledOn($.fn.scrollintoview, sinon.match(highlight))

    describe 'on "getDocumentInfo" event', ->
      guest = null

      beforeEach ->
        sandbox.stub(document, 'title', 'hi')
        guest = createGuest()
        guest.plugins.PDF =
          uri: sandbox.stub().returns(window.location.href)
          getMetadata: sandbox.stub()

      afterEach ->
        sandbox.restore()

      it 'calls the callback with the href and pdf metadata', (done) ->
        assertComplete = (payload) ->
          try
            assert.equal(payload.uri, document.location.href)
            assert.equal(payload.metadata, metadata)
            done()
          catch e
            done(e)

        ctx = {complete: assertComplete, delayReturn: sandbox.stub()}
        metadata = {title: 'hi'}
        promise = Promise.resolve(metadata)
        guest.plugins.PDF.getMetadata.returns(promise)

        emitGuestEvent('getDocumentInfo', ctx)

      it 'calls the callback with the href and basic metadata if pdf fails', (done) ->
        assertComplete = (payload) ->
          try
            assert.equal(payload.uri, window.location.href)
            assert.deepEqual(payload.metadata, metadata)
            done()
          catch e
            done(e)

        ctx = {complete: assertComplete, delayReturn: sandbox.stub()}
        metadata = {title: 'hi', link: [{href: window.location.href}]}

        promise = Promise.reject(new Error('Not a PDF document'))
        guest.plugins.PDF.getMetadata.returns(promise)

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

  describe 'createAnnotation()', ->
    it 'adds metadata to the annotation object', (done) ->
      guest = createGuest()
      sinon.stub(guest, 'getDocumentInfo').returns(Promise.resolve({
        metadata: {title: 'hello'}
        uri: 'http://example.com/'
      }))
      annotation = {}
      guest.createAnnotation(annotation)
      setTimeout ->
        assert.equal(annotation.uri, 'http://example.com/')
        assert.deepEqual(annotation.document, {title: 'hello'})
        done()

    it 'treats an argument as the annotation object', ->
      guest = createGuest()
      annotation = {foo: 'bar'}
      annotation = guest.createAnnotation(annotation)
      assert.equal(annotation.foo, 'bar')

  describe 'setupAnnotation()', ->
    el = null
    range = null

    beforeEach ->
      el = document.createElement('span')
      txt = document.createTextNode('hello')
      el.appendChild(txt)
      document.body.appendChild(el)
      range = document.createRange()
      range.selectNode(el)

    afterEach ->
      document.body.removeChild(el)

    it "doesn't declare annotation without targets as orphans", (done) ->
      guest = createGuest()
      annotation = target: []
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        assert.isFalse(annotation.$orphan)
        done()

    it "doesn't declare annotations with a working target as orphans", (done) ->
      guest = createGuest()
      annotation = target: [{selector: "test"}]
      sandbox.stub(anchoring, 'anchor').returns(range)
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        assert.isFalse(annotation.$orphan)
        done()

    it "declares annotations with broken targets as orphans", (done) ->
      guest = createGuest()
      annotation = target: [{selector: 'broken selector'}]
      sandbox.stub(anchoring, 'anchor').throws()
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        assert.isTrue(annotation.$orphan)
        done()

    it 'updates the cross frame and bucket bar plugins', (done) ->
      guest = createGuest()
      guest.plugins.CrossFrame =
        sync: sinon.stub()
      guest.plugins.BucketBar =
        update: sinon.stub()
      annotation = {}
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        assert.called(guest.plugins.BucketBar.update)
        assert.called(guest.plugins.CrossFrame.sync)
        done()

    it 'saves the anchor positions on the annotation', (done) ->
      guest = createGuest()
      sandbox.stub(anchoring, 'anchor').returns(range)
      clientRect = {top: 100, left: 200}
      window.scrollX = 50
      window.scrollY = 25
      sandbox.stub(highlighter, 'getBoundingClientRect').returns(clientRect)
      annotation = guest.setupAnnotation({target: [{selector: []}]})
      waitForSync(annotation).then ->
        assert.equal(annotation.$anchors.length, 1)
        pos = annotation.$anchors[0].pos
        assert.equal(pos.top, 125)
        assert.equal(pos.left, 250)
        done()

    it 'adds the anchor to the "anchors" instance property"', (done) ->
      guest = createGuest()
      highlights = [document.createElement('span')]
      sandbox.stub(anchoring, 'anchor').returns(range)
      sandbox.stub(highlighter, 'highlightRange').returns(highlights)
      target = [{selector: []}]
      annotation = guest.setupAnnotation({target: [target]})
      waitForSync(annotation).then ->
        assert.equal(guest.anchors.length, 1)
        assert.strictEqual(guest.anchors[0].annotation, annotation)
        assert.strictEqual(guest.anchors[0].target, target)
        assert.strictEqual(guest.anchors[0].range, range)
        assert.strictEqual(guest.anchors[0].highlights, highlights)
        done()

    it 'destroys targets that have been removed from the annotation', (done) ->
      annotation = {}
      target = {}
      highlights = []
      guest = createGuest()
      guest.anchors = [{annotation, target, highlights}]
      removeHighlights = sandbox.stub(highlighter, 'removeHighlights')
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        assert.equal(guest.anchors.length, 0)
        assert.calledWith(removeHighlights, highlights)
        done()

    it 'does not reanchor targets that are already anchored', (done) ->
      guest = createGuest()
      annotation = target: [{selector: "test"}]
      stub = sandbox.stub(anchoring, 'anchor').returns(range)
      guest.setupAnnotation(annotation)
      waitForSync(annotation).then ->
        delete annotation.$anchors
        guest.setupAnnotation(annotation)
        waitForSync(annotation).then ->
          assert.equal(guest.anchors.length, 1)
          assert.calledOnce(stub)
          done()
