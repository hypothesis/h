assert = chai.assert

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

  constructor: (manager, annotation, target) ->
    super manager, annotation, target, 42, 42,
      "fake quote for" + target.id

    @id = "fake anchor for " + target.id

describe 'Annotator.Plugin.EnhancedAnchoring', ->
  sandbox = null

  createAnchoringManager = ->
    annotator =
      publish: (event) ->

    am = new Annotator.Plugin.EnhancedAnchoring()
    am.annotator = annotator
    am.pluginInit()

    am.chooseAccessPolicy()

    am.strategies.push
      name: "dummy anchoring strategy"
      code: (annotation, target) ->
        new TestAnchor am, annotation, target

    am

  createTestAnnotation = (id, targets = 1) ->
    id: "annotation " + id
    target: (("target " + id + "-" + num) for num in [1 .. targets])
    anchors: []

  beforeEach ->
    sandbox = sinon.sandbox.create()
    sandbox.stub Annotator.TextHighlight, 'createFrom',
      (segment, anchor, page) -> {segment, anchor, page}

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
