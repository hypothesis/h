Annotator = require('annotator')
Host = require('../host')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'Annotator.Host', ->
  sandbox = sinon.sandbox.create()
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
    fakeCrossFrame.notify = sandbox.stub().returns(fakeCrossFrame)

    sandbox.stub(Annotator.Plugin, 'CrossFrame').returns(fakeCrossFrame)

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

  describe 'crossframe listeners', ->
    emitHostEvent = (event, args...) ->
      fn(args...) for [evt, fn] in fakeCrossFrame.on.args when event == evt

    describe 'on "showFrame" event', ->
      it 'shows the frame', ->
        target = sandbox.stub(Annotator.Host.prototype, 'showFrame')
        host = createHost()
        emitHostEvent('showFrame')
        assert.called(target)

    describe 'on "hideFrame" event', ->
      it 'hides the frame', ->
        target = sandbox.stub(Annotator.Host.prototype, 'hideFrame')
        host = createHost()
        emitHostEvent('hideFrame')
        assert.called(target)
