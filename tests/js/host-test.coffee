assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Host', ->
  createHost = (options) ->
    element = document.createElement('div')
    return new Annotator.Host(element, options)

  # Disable Annotator's ridiculous logging.
  before -> sinon.stub(console, 'log')
  after  -> console.log.restore()

  describe 'options', ->
    it 'enables highlighting when showHighlights option is provided', (done) ->
      host = createHost(showHighlights: true)
      host.on 'panelReady', ->
        assert.isTrue(host.visibleHighlights)
        done()
      host.publish('panelReady')

    it 'does not enable highlighting when no showHighlights option is provided', (done) ->
      host = createHost({})
      host.on 'panelReady', ->
        assert.isFalse(host.visibleHighlights)
        done()
      host.publish('panelReady')
