bb = require('../../../../h/static/scripts/annotator/plugin/bucket-bar')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.BucketBar', ->
  createBucketBar = (options) ->
    element = document.createElement('div')
    new bb.BucketBar(element, options || {})

  # Yes this is testing a private method. Yes this is bad practice, but I'd
  # rather test this functionality in a private method than not test it at all.
  describe '_buildTabs', ->
    setup = (tabs) ->
      bucketBar = createBucketBar()
      bucketBar.tabs = tabs
      bucketBar.buckets = [['AN ANNOTATION?']]
      bucketBar.index = [
        0,
        bucketBar.BUCKET_THRESHOLD_PAD - 12,
        bucketBar.BUCKET_THRESHOLD_PAD + bucketBar.BUCKET_SIZE + 6
      ]
      bucketBar

    it 'creates a tab with a title', ->
      tab = $('<div />')
      bucketBar = setup(tab)

      bucketBar._buildTabs()
      assert.equal(tab.attr('title'), 'Show one annotation')

    it 'creates a tab with a pluralized title', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      bucketBar.buckets[0].push('Another Annotation?')

      bucketBar._buildTabs()
      assert.equal(tab.attr('title'), 'Show 2 annotations')

    it 'sets the tab text to the number of annotations', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      bucketBar.buckets[0].push('Another Annotation?')

      bucketBar._buildTabs()
      assert.equal(tab.text(), '2')

    it 'sets the tab text to the number of annotations', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      bucketBar.buckets[0].push('Another Annotation?')

      bucketBar._buildTabs()
      assert.equal(tab.text(), '2')

    it 'adds the class "upper" if the annotation is at the top', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      sinon.stub(bucketBar, 'isUpper').returns(true)

      bucketBar._buildTabs()
      assert.equal(tab.hasClass('upper'), true)

    it 'removes the class "upper" if the annotation is not at the top', ->
      tab = $('<div />').addClass('upper')
      bucketBar = setup(tab)
      sinon.stub(bucketBar, 'isUpper').returns(false)

      bucketBar._buildTabs()
      assert.equal(tab.hasClass('upper'), false)

    it 'adds the class "lower" if the annotation is at the top', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      sinon.stub(bucketBar, 'isLower').returns(true)

      bucketBar._buildTabs()
      assert.equal(tab.hasClass('lower'), true)

    it 'removes the class "lower" if the annotation is not at the top', ->
      tab = $('<div />').addClass('lower')
      bucketBar = setup(tab)
      sinon.stub(bucketBar, 'isLower').returns(false)

      bucketBar._buildTabs()
      assert.equal(tab.hasClass('lower'), false)

    it 'reveals the tab if there are annotations in the bucket', ->
      tab = $('<div />')
      bucketBar = setup(tab)

      bucketBar._buildTabs()
      assert.equal(tab.css('display'), '')

    it 'hides the tab if there are no annotations in the bucket', ->
      tab = $('<div />')
      bucketBar = setup(tab)
      bucketBar.buckets = []

      bucketBar._buildTabs()
      assert.equal(tab.css('display'), 'none')
