assert = chai.assert
sinon.assert.expose(assert, prefix: '')

# In order to be able to create highlights,
# the Annotator.TextHighlight class must exist.
# This class is registered then the TextHighlights plugin
# is initialized, so we will do that.
th = new Annotator.Plugin.TextHighlights()
th.pluginInit()

describe 'Annotator.Plugin.TextHighlight', ->
  sandbox = null
  jqElement = null
  scrollTarget = null

  createTestHighlight = ->
    anchor =
      id: "test anchor"
      annotation: "test annotation"
      anchoring:
        id: "test anchoring manager"
        annotator:
          id: "test annotator"
          element:
            delegate: sinon.spy()

    new Annotator.TextHighlight anchor, "test page", "test range"

  beforeEach ->
    sandbox = sinon.sandbox.create()
    sandbox.stub Annotator.TextHighlight, 'highlightRange',
      (normedRange, cssClass) -> "test highlight span"

    sandbox.stub Annotator.$.fn, "init", (selector, context) ->
      jqElement =
        selector: selector
        data: sinon.spy()
        scrollintoview: sinon.spy (options) ->
          scrollTarget = this.selector
          options?.complete?()

  afterEach ->
    sandbox.restore()
    scrollTarget = null

  describe "constructor", ->
    it 'wraps a highlight span around the given range', ->
      hl = createTestHighlight()
      assert.calledWith Annotator.TextHighlight.highlightRange, "test range"

    it 'stores the created highlight spans in _highlights', ->
      hl = createTestHighlight()
      assert.equal hl._highlights, "test highlight span"

    it "wraps a jQuery element around the highlight span", ->
      hl = createTestHighlight()
      assert.equal jqElement.selector, "test highlight span"

    it "assigns the annotation as data to the highlight span", ->
      hl = createTestHighlight()
      assert.calledWith jqElement.data, "annotation", "test annotation"

  describe "scrollIntoView", ->

    it 'calls jQuery scrollintoview', ->
      hl = createTestHighlight()
      hl.scrollIntoView()
      assert.called jqElement.scrollintoview

    it 'scrolls to the created highlight span', ->
      hl = createTestHighlight()
      hl.scrollIntoView()
      assert.equal scrollTarget, hl._highlights

    it 'resolves the promise after scrolling', ->
      hl = createTestHighlight()
      hl.scrollIntoView().then ->
        assert.ok scrollTarget
