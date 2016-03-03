Annotator = require('annotator')

proxyquire = require('proxyquire')
Host = proxyquire('../host', {
  'annotator': Annotator,
})

describe 'Host', ->
  sandbox = sinon.sandbox.create()
  CrossFrame = null
  fakeCrossFrame = null

  createHost = (options={}, element=null) ->
    if !element
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

  describe 'focus', ->
    element = null
    frame = null
    host = null

    beforeEach ->
      element = document.createElement('div')
      document.body.appendChild(element)
      host = createHost({}, element)
      frame = element.querySelector('[name=hyp_sidebar_frame]')
      sinon.spy(frame.contentWindow, 'focus')

    afterEach ->
      frame.contentWindow.focus.restore()
      element.parentNode.removeChild(element)

    it 'focuses the sidebar when a new annotation is created', ->
      host.publish('beforeAnnotationCreated', [{
        $highlight: false,
      }])
      assert.called(frame.contentWindow.focus)

    it 'does not focus the sidebar when a new highlight is created', ->
      host.publish('beforeAnnotationCreated', [{
        $highlight: true,
      }])
      assert.notCalled(frame.contentWindow.focus)

  describe 'options', ->
    it 'disables highlighting if showHighlights: false is given', (done) ->
      host = createHost(showHighlights: false)
      host.on 'panelReady', ->
        assert.isFalse(host.visibleHighlights)
        done()
      host.publish('panelReady')

    it 'enables highlighting when no showHighlights option is given', (done) ->
      host = createHost({})
      host.on 'panelReady', ->
        assert.isTrue(host.visibleHighlights)
        done()
      host.publish('panelReady')
