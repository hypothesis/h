assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Heatmap', ->
  createHeatmap = (options) ->
    element = document.createElement('div')
    new Annotator.Plugin.Heatmap(element, options || {})

  # Yes this is testing a private method. Yes this is bad practice, but I'd
  # rather test this functionality in a private method than not test it at all.
  describe '_buildTabs', ->
    setup = (tabs) ->
      heatmap = createHeatmap()
      heatmap.tabs = tabs
      heatmap.buckets = [['AN ANNOTATION?']]
      heatmap.index = [
        0,
        heatmap.BUCKET_THRESHOLD_PAD - 12,
        heatmap.BUCKET_THRESHOLD_PAD + heatmap.BUCKET_SIZE + 6
      ]
      heatmap

    it 'creates a tab with a title', ->
      tab = $('<div />')
      heatmap = setup(tab)

      heatmap._buildTabs()
      assert.equal(tab.attr('title'), 'Show one annotation')

    it 'creates a tab with a pluralized title', ->
      tab = $('<div />')
      heatmap = setup(tab)
      heatmap.buckets[0].push('Another Annotation?')

      heatmap._buildTabs()
      assert.equal(tab.attr('title'), 'Show 2 annotations')

    it 'sets the tab text to the number of annotations', ->
      tab = $('<div />')
      heatmap = setup(tab)
      heatmap.buckets[0].push('Another Annotation?')

      heatmap._buildTabs()
      assert.equal(tab.text(), '2')

    it 'sets the tab text to the number of annotations', ->
      tab = $('<div />')
      heatmap = setup(tab)
      heatmap.buckets[0].push('Another Annotation?')

      heatmap._buildTabs()
      assert.equal(tab.text(), '2')

    it 'adds the class "upper" if the annotation is at the top', ->
      tab = $('<div />')
      heatmap = setup(tab)
      sinon.stub(heatmap, 'isUpper').returns(true)

      heatmap._buildTabs()
      assert.equal(tab.hasClass('upper'), true)

    it 'removes the class "upper" if the annotation is not at the top', ->
      tab = $('<div />').addClass('upper')
      heatmap = setup(tab)
      sinon.stub(heatmap, 'isUpper').returns(false)

      heatmap._buildTabs()
      assert.equal(tab.hasClass('upper'), false)

    it 'adds the class "lower" if the annotation is at the top', ->
      tab = $('<div />')
      heatmap = setup(tab)
      sinon.stub(heatmap, 'isLower').returns(true)

      heatmap._buildTabs()
      assert.equal(tab.hasClass('lower'), true)

    it 'removes the class "lower" if the annotation is not at the top', ->
      tab = $('<div />').addClass('lower')
      heatmap = setup(tab)
      sinon.stub(heatmap, 'isLower').returns(false)

      heatmap._buildTabs()
      assert.equal(tab.hasClass('lower'), false)

    it 'reveals the tab if there are annotations in the bucket', ->
      tab = $('<div />')
      heatmap = setup(tab)

      heatmap._buildTabs()
      assert.equal(tab.css('display'), '')

    it 'hides the tab if there are no annotations in the bucket', ->
      tab = $('<div />')
      heatmap = setup(tab)
      heatmap.buckets = []

      heatmap._buildTabs()
      assert.equal(tab.css('display'), 'none')
