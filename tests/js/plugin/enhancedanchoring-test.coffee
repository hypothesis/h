assert = chai.assert
sinon.assert.expose(assert, prefix: '')

# In order to be able to create highlights,
# the Annotator.TextHighlight class must exist.
# This class is registered then the TextHighlights plugin
# is initialized, so we will do that.
th = new Annotator.Plugin.TextHighlights()
th.pluginInit()

# Then Anchor class is not supposed to be used directly.
# Every concrete implementation should have it's own class,
# encompassing a way to identify the given segment of the document.
#
# For testing, we will use the TestAnchor class,
# which does not actually identify a real segment of the HTML document.
class TestAnchor extends Annotator.Anchor

  _getSegment: -> "html segment for " + @id

  constructor: (manager, annotation, target, startPage, endPage) ->
    super manager, annotation, target, startPage, endPage,
      "fake quote for" + target.id

    @id = "fake anchor for " + target.id

describe 'Annotator.Plugin.EnhancedAnchoring', ->
  sandbox = null

  createAnchoringManager = ->
    annotator =
      publish: sinon.spy()

    am = new Annotator.Plugin.EnhancedAnchoring()
    am.annotator = annotator
    am.pluginInit()

    am.chooseAccessPolicy()

    am.document.setPageIndex = sinon.spy()

    am.strategies.push
      name: "dummy anchoring strategy"
      code: (annotation, target) ->
        new TestAnchor am, annotation, target, 42, 42

    am

  createTestAnnotation = (id, targets = 1) ->
    id: "annotation " + id
    target: (("target " + id + "-" + num) for num in [1 .. targets])
    anchors: []

  beforeEach ->
    sandbox = sinon.sandbox.create()
    sandbox.stub Annotator.TextHighlight, 'createFrom',
      (segment, anchor, page) ->
        segment: segment
        anchor: anchor
        page: page
        removeFromDocument: sinon.spy()
        scrollIntoView: sinon.spy ->
          new Promise (resolve, reject) ->
            setTimeout ->
              anchor.anchoring.document.setPageIndex page
              resolve()

  afterEach ->
    sandbox.restore()

  describe "createAnchor", ->

    it 'adds an anchor property to the annotations', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1", 2

      anchor1 = am.createAnchor(ann, ann.target[0]).result
      anchor2 = am.createAnchor(ann, ann.target[1]).result

      assert.isArray ann.anchors
      assert.include ann.anchors, anchor1
      assert.include ann.anchors, anchor2
      assert.equal ann.anchors.length, 2

    it 'adds an annotation property to the created anchors', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result
      assert.equal anchor.annotation, ann

    it 'adds a target property to the created anchors', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result

      assert.equal anchor.target, ann.target[0]

    it 'creates the anchors from the right targets', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result
      assert.equal anchor.id, "fake anchor for " + anchor.target.id

    it 'adds the created anchors to the correct per-page array', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result
      assert.include am.anchors[anchor.startPage], anchor

    it 'adds the created highlights to the anchors', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result

      assert.isObject anchor.highlight
      page = anchor.startPage
      hl = anchor.highlight[page]
      assert.ok hl
      assert.equal hl.page, page

    it 'announces the creation of the highlights in an event', ->
      am = createAnchoringManager()

      assert.notCalled am.annotator.publish

      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result

      hl = anchor.highlight[anchor.startPage]
      assert.calledWith am.annotator.publish, 'highlightsCreated', [hl]

    it 'adds an anchor property to the created Highlights', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result

      page = anchor.startPage
      hl = anchor.highlight[page]
      assert.equal hl.anchor, anchor

  describe "getAnchors", ->

    it 'returns an empty array by default', ->
      am = createAnchoringManager()
      anchors = am.getAnchors()
      assert.isArray anchors
      assert.equal anchors.length, 0

    it 'returns all the anchors', ->
      am = createAnchoringManager()

      ann1 = createTestAnnotation "a1", 2
      ann2 = createTestAnnotation "a2"
      ann3 = createTestAnnotation "a3"
      anchor11 = am.createAnchor(ann1, ann1.target[0]).result
      anchor12 = am.createAnchor(ann1, ann1.target[1]).result
      anchor2 = am.createAnchor(ann2, ann2.target).result
      anchor3 = am.createAnchor(ann3, ann2.target).result

      anchors = am.getAnchors()

      assert.isArray anchors
      assert.include anchors, anchor11
      assert.include anchors, anchor12
      assert.include anchors, anchor2
      assert.include anchors, anchor3

    it 'returns the anchors belonging to a set of annotations', ->
      am = createAnchoringManager()
      ann1 = createTestAnnotation "a1", 2
      ann2 = createTestAnnotation "a2"
      ann3 = createTestAnnotation "a3"
      anchor11 = am.createAnchor(ann1, ann1.target[0]).result
      anchor12 = am.createAnchor(ann1, ann1.target[1]).result
      anchor2 = am.createAnchor(ann2, ann2.target).result
      anchor3 = am.createAnchor(ann3, ann2.target).result

      anchors = am.getAnchors [ann1, ann2]

      assert.isArray anchors
      assert.include anchors, anchor11
      assert.include anchors, anchor12
      assert.include anchors, anchor2
      assert.notInclude anchors, anchor3

  describe 'getHighlights', ->
    it 'returns an empty array by default', ->
      am = createAnchoringManager()
      hls = am.getHighlights()
      assert.isArray hls
      assert.equal hls.length, 0

    it 'returns all the highlights', ->
      am = createAnchoringManager()
      ann1 = createTestAnnotation "a1", 2
      ann2 = createTestAnnotation "a2"
      ann3 = createTestAnnotation "a3"
      anchor11 = am.createAnchor(ann1, ann1.target[0]).result
      anchor12 = am.createAnchor(ann1, ann1.target[1]).result
      anchor2 = am.createAnchor(ann2, ann2.target).result
      anchor3 = am.createAnchor(ann3, ann2.target).result

      hls = am.getHighlights()

      assert.isArray hls
      assert.include hls, anchor11.highlight[anchor11.startPage]
      assert.include hls, anchor12.highlight[anchor12.startPage]
      assert.include hls, anchor2.highlight[anchor2.startPage]
      assert.include hls, anchor3.highlight[anchor3.startPage]

    it 'returns the highlights belonging to a set of annotations', ->
      am = createAnchoringManager()
      ann1 = createTestAnnotation "a1", 2
      ann2 = createTestAnnotation "a2"
      ann3 = createTestAnnotation "a3"
      anchor11 = am.createAnchor(ann1, ann1.target[0]).result
      anchor12 = am.createAnchor(ann1, ann1.target[1]).result
      anchor2 = am.createAnchor(ann2, ann2.target).result
      anchor3 = am.createAnchor(ann3, ann2.target).result

      hls = am.getHighlights [ann1, ann2]

      assert.isArray hls
      assert.include hls, anchor11.highlight[anchor11.startPage]
      assert.include hls, anchor12.highlight[anchor12.startPage]
      assert.include hls, anchor2.highlight[anchor2.startPage]
      assert.notInclude hls, anchor3.highlight[anchor3.startPage]

  describe 'Anchor.scrollIntoView()', ->
    it 'calls scrollIntoView() on the highlight', ->
      am = createAnchoringManager()
      ann = createTestAnnotation "a1"
      anchor = am.createAnchor(ann, ann.target[0]).result
      anchor.scrollIntoView().then ->

        assert.called anchor.highlight[anchor.startPage].scrollIntoView

  describe 'two-phased anchoring', ->

    # Simple lazy rendering document simulation for testing,
    # which emulates the user movement prediction (and page rendering)
    # behavior of PDF.js
    class DummyDocumentAccess

      @applicable: -> true

      isPageMapped: (index) -> index in @_rendered
      getPageIndex: -> @currentIndex

      setPageIndex: sinon.spy()

      constructor: ->
        @_rendered = []
        @currentIndex = -10

    # Helper function to trigger a page rendering
    # This is an asynchronous method; returns a promise.
    renderPage = (doc, index) ->
      if doc.isPageMapped(index)
        throw new Error "Cannot call renderPage with an already mapped index: #{index}, ensure the document is setup correctly"

      new Promise (resolve, reject) ->
        setTimeout ->
          doc._rendered.push index

          # Publish an event
          event = document.createEvent "UIEvents"
          event.initUIEvent "docPageMapped", false, false, window, 0
          event.pageIndex = index
          window.dispatchEvent event

          # Resolve the promise
          resolve()

    # Helper function to trigger the rendering of several pages.
    # This is an asynchronous method; returns a promise.
    renderPages = (doc, indexes) ->
      Promise.all(renderPage(doc, index) for index in indexes)

    # Helper function to trigger a page unrendering
    # This is an asynchronous method; returns a promise.
    unrenderPage = (doc, index) ->
      unless doc.isPageMapped index
        throw new Error "Cannot call unrenderPage with an unmapped index: #{index}, ensure the document is setup correctly"

      new Promise (resolve, reject) ->
        setTimeout ->
          i = doc._rendered.indexOf index

          doc._rendered.splice(i, 1)

          # Publish an event
          event = document.createEvent "UIEvents"
          event.initUIEvent "docPageUnmapped", false, false, window, 0
          event.pageIndex = index
          window.dispatchEvent event

          # Resolve the promise
          resolve()

    # Helper function to set up an anchoring manager
    # with a document access policy that mimics
    # a platform with lazy rendering
    createAnchoringManagerAndLazyDocument = ->
      annotator =
        publish: sinon.spy()

      am = new Annotator.Plugin.EnhancedAnchoring()
      am.annotator = annotator
      am.pluginInit()

      am.documentAccessStrategies.unshift
        name: "Dummy two-phase"
        mapper: DummyDocumentAccess

      am.strategies.push
        name: "dummy anchoring strategy"
        code: (annotation, target) ->
          new TestAnchor am, annotation, target,
            target.startPage, target.endPage

      am.chooseAccessPolicy()

      am

    # Helper function to create an annotation with several
    # targets, search of them potentially targeting a given
    # range of pages.
    createTestAnnotationForPages = (id, pageRanges) ->
      result =
        id: "annotation " + id
        target: []
        anchors: []

      index = 0
      for targetRange in pageRanges
        [start, end] = if Array.isArray targetRange
          targetRange
        else
          [targetRange, targetRange]
        result.target.push
          id: "target " + id + "-" + index++
          startPage: start
          endPage: end

      result

    describe "when the wanted page is already rendered", ->

      it 'creates real anchors', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          assert anchor.fullyRealized

      it 'creates highlights', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]
          assert.ok hl
          assert.equal hl.page, 1

      it 'announces the highlights with the appropriate event', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]

          assert.calledWith am.annotator.publish, 'highlightsCreated', [hl]

    describe 'when a page is unrendered', ->

      it 'calls removeFromDocument an the correct highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]
          unrenderPage(am.document, 1).then ->

            assert.called hl.removeFromDocument

      it 'removes highlights from the relevant page', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          unrenderPage(am.document, 1).then ->

            assert !anchor.fullyRealized

      it 'announces the removal of the highlights from the relevant page', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]
          unrenderPage(am.document, 1).then ->
            assert.calledWith am.annotator.publish, 'highlightRemoved', hl

      it 'switches the anchor to virtual', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          unrenderPage(am.document, 1).then ->
            assert !anchor.fullyRealized

    describe 'when the wanted page is not rendered', ->

      it 'creates virtual anchors', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [1]
        anchor = am.createAnchor(ann, ann.target[0]).result

        assert !anchor.fullyRealized

      it 'creates no highlights', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [1]
        anchor = am.createAnchor(ann, ann.target[0]).result

        assert.notOk anchor.highlight[1], "Should not have a highlight on page 1"

      it 'announces no highlihts', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [1]
        anchor = am.createAnchor(ann, ann.target[0]).result

        assert.notCalled am.annotator.publish

      describe 'when the pages are rendered later on', ->

        it 'realizes the anchor', ->
          am = createAnchoringManagerAndLazyDocument()
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          renderPage(am.document, 1).then ->
            assert anchor.fullyRealized

        it 'creates the highlight', ->
          am = createAnchoringManagerAndLazyDocument()
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          renderPage(am.document, 1).then ->
            hl = anchor.highlight[1]
            assert.ok hl
            assert.calledWith am.annotator.publish, 'highlightsCreated', [hl]

        it 'announces the highlight', ->
          am = createAnchoringManagerAndLazyDocument()
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          renderPage(am.document, 1).then ->
            hl = anchor.highlight[1]
            assert.calledWith am.annotator.publish, 'highlightsCreated', [hl]

    describe 'when an anchor spans several pages, some of them rendered', ->

      it 'creates partially realized anchors', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 2).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result

          assert !anchor.fullyRealized

      it 'creates the highlights for the rendered pages', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 2).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result

          assert.ok anchor.highlight[2]

      it 'creates no highlights for the missing pages', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 2).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result

          assert.notOk anchor.highlight[3]

      it 'announces the creation of highlights for the rendered pages', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 2).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result

          assert.calledWith am.annotator.publish,
            'highlightsCreated', [anchor.highlight[2]]

      describe 'when the missing pages are rendered', ->

        it 'the anchor is fully realized', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 2).then ->
            ann = createTestAnnotationForPages "a1", [[2,3]]
            anchor = am.createAnchor(ann, ann.target[0]).result
            renderPage(am.document, 3).then ->

              assert anchor.fullyRealized

        it 'creates the missing highlights', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 2).then ->
            ann = createTestAnnotationForPages "a1", [[2,3]]
            anchor = am.createAnchor(ann, ann.target[0]).result
            renderPage(am.document, 3).then ->

              assert.ok anchor.highlight[3]

        it 'announces the creation of the missing highlights', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 2).then ->
            ann = createTestAnnotationForPages "a1", [[2,3]]
            anchor = am.createAnchor(ann, ann.target[0]).result

            renderPage(am.document, 3).then ->

              assert.calledWith am.annotator.publish,
                'highlightsCreated', [anchor.highlight[3]]

    describe 'when an achor spans several pages, and a page is unrendered', ->

      it 'calls removeFromDocument() on the involved highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2,3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[2]
          unrenderPage(am.document, 2).then ->

            assert.called hl.removeFromDocument

      it 'does not call removeFromDocument() on the other highlights', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2,3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[3]
          unrenderPage(am.document, 2).then ->

            assert.notCalled hl.removeFromDocument

      it 'removes the involved highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2, 3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          unrenderPage(am.document, 2).then ->

            assert.notOk anchor.highlight[2]

      it 'retains the other highlights', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2,3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          unrenderPage(am.document, 2).then ->

          assert.ok anchor.highlight[3]

      it 'announces the removal of the involved highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2, 3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[2]
          unrenderPage(am.document, 2).then ->

            assert.calledWith am.annotator.publish, 'highlightRemoved', hl

      it 'switched the anchor to virtual', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPages(am.document, [2, 3]).then ->
          ann = createTestAnnotationForPages "a1", [[2,3]]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[2]
          unrenderPage(am.document, 2).then ->

            assert !anchor.fullyRealized

    describe 'manually virtualizing an anchor', ->

      it 'calls removeFromDocument() on the highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]
          anchor.virtualize 1

          assert.called hl.removeFromDocument

      it 'removes the highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          anchor.virtualize 1

          assert.notOk anchor.highlight[1], "the highlight should be no more"

      it 'announces the removal of the highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          hl = anchor.highlight[1]
          anchor.virtualize 1

          assert.calledWith am.annotator.publish, 'highlightRemoved', hl

      it 'switches the anchor to virtual', ->
        am = createAnchoringManagerAndLazyDocument()
        renderPage(am.document, 1).then ->
          ann = createTestAnnotationForPages "a1", [1]
          anchor = am.createAnchor(ann, ann.target[0]).result
          anchor.virtualize 1

          assert !anchor.fullyRealized

      describe 'when re-realizing a manually virtualized anchor', ->

        it 're-creates the highlight', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 1).then ->
            ann = createTestAnnotationForPages "a1", [1]
            anchor = am.createAnchor(ann, ann.target[0]).result
            anchor.virtualize 1
            anchor.realize()

            assert.ok anchor.highlight[1]

        it 'announces the creation of the highlight', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 1).then ->
            ann = createTestAnnotationForPages "a1", [1]
            anchor = am.createAnchor(ann, ann.target[0]).result
            anchor.virtualize 1
            anchor.realize()

            hl = anchor.highlight[1]
            assert.calledWith am.annotator.publish, 'highlightsCreated', [hl]

        it 'realizes the anchor', ->
          am = createAnchoringManagerAndLazyDocument()
          renderPage(am.document, 1).then ->
            ann = createTestAnnotationForPages "a1", [1]
            anchor = am.createAnchor(ann, ann.target[0]).result
            anchor.virtualize 1
            anchor.realize()

            assert anchor.fullyRealized

    describe 'when scrolling to a virtual anchor', ->

      it 'jumpings close to the wanted page', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [10]
        anchor = am.createAnchor(ann, ann.target[0]).result
        am.document.currentIndex = 5  # We start from page 5
        am.document.setPageIndex = sinon.spy (index) ->
          am.document.currentIndex = index
          if index is 9
            renderPage am.document, 9
            renderPage am.document, 10

        # Now we trigger the actual action
        anchor.scrollIntoView().then ->
          assert.calledWith am.document.setPageIndex, 9

      it 'has the wanted page rendered', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [10]
        anchor = am.createAnchor(ann, ann.target[0]).result
        am.document.currentIndex = 5  # We start from page 5
        am.document.setPageIndex = sinon.spy (index) ->
          am.document.currentIndex = index
          if index is 9
            renderPage am.document, 9
            renderPage am.document, 10

        # Now we trigger the actual action
        anchor.scrollIntoView().then ->
          assert am.document.isPageMapped 10

      it 'gets to the wanted page, eventually', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [10]
        anchor = am.createAnchor(ann, ann.target[0]).result
        am.document.currentIndex = 5  # We start from page 5
        am.document.setPageIndex = sinon.spy (index) ->
          am.document.currentIndex = index
          if index is 9
            renderPage am.document, 9
            renderPage am.document, 10

        # Now we trigger the actual action
        anchor.scrollIntoView().then ->
          assert.calledWith am.document.setPageIndex, 10

      it 'calls scrollIntoView() on the highlight', ->
        am = createAnchoringManagerAndLazyDocument()
        ann = createTestAnnotationForPages "a1", [10]
        anchor = am.createAnchor(ann, ann.target[0]).result
        am.document.currentIndex = 5  # We start from page 5
        am.document.setPageIndex = sinon.spy (index) ->
          am.document.currentIndex = index
          if index is 9
            renderPage am.document, 9
            renderPage am.document, 10

        anchor.scrollIntoView().then ->
          assert.called anchor.highlight[10].scrollIntoView
