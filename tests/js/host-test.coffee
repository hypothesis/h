assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Host', ->
  sandbox = sinon.sandbox.create()

  createHost = (options) ->
    element = document.createElement('div')
    return new Annotator.Host(element, options)

  beforeEach ->
    # Disable Annotator's ridiculous logging.
    sandbox.stub(console, 'log')

    fakeBridge =
      onConnect: sandbox.stub()
      on: sandbox.stub()

    sandbox.stub(Annotator.Plugin, 'Bridge').returns(fakeBridge)

  afterEach -> sandbox.restore()

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
