Annotator = require('annotator')

proxyquire = require('proxyquire')
Host = proxyquire('../host', {
  'annotator': Annotator,
})

describe 'Host', ->
  sandbox = sinon.sandbox.create()
  CrossFrame = null
  fakeCrossFrame = null

  createHost = (options={}) ->
    element = document.createElement('div')
    return new Host(element, options)

  beforeEach ->
    # Disable Annotator's ridiculous logging.
    sandbox.stub(console, 'log')

    fakeCrossFrame = {}
    fakeCrossFrame.onConnect = sandbox.stub().returns(fakeCrossFrame)
    fakeCrossFrame.on = sandbox.stub().returns(fakeCrossFrame)
    fakeCrossFrame.call = sandbox.spy()

    CrossFrame = sandbox.stub()
    CrossFrame.returns(fakeCrossFrame)
    Annotator.Plugin.CrossFrame = CrossFrame

  afterEach ->
    sandbox.restore()
    delete Annotator.Plugin.CrossFrame

  describe 'widget visibility', ->
    it 'starts hidden', ->
      host = createHost()
      assert.equal(host.frame.css('display'), 'none')

    it 'becomes visible when the "panelReady" event fires', ->
      host = createHost()
      host.publish('panelReady')
      assert.equal(host.frame.css('display'), '')

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
