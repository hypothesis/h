Annotator = require('annotator')
Host = require('../host')

describe 'Host', ->
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

    Annotator.Plugin.CrossFrame = -> fakeCrossFrame

  afterEach -> sandbox.restore()

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

  describe 'crossframe listeners', ->
    emitHostEvent = (event, args...) ->
      fn(args...) for [evt, fn] in fakeCrossFrame.on.args when event == evt

    describe 'on "showFrame" event', ->
      it 'shows the frame', ->
        target = sandbox.stub(Host.prototype, 'showFrame')
        host = createHost()
        emitHostEvent('showFrame')
        assert.called(target)

    describe 'on "hideFrame" event', ->
      it 'hides the frame', ->
        target = sandbox.stub(Host.prototype, 'hideFrame')
        host = createHost()
        emitHostEvent('hideFrame')
        assert.called(target)

  describe 'pan gestures', ->
    host = null

    beforeEach ->
      host = createHost({})

    describe 'panstart event', ->
      beforeEach ->
        sandbox.stub(window, 'getComputedStyle').returns({marginLeft: '100px'})
        host.onPan({type: 'panstart'})

      it 'disables pointer events and transitions on the widget', ->
        assert.isTrue(host.frame.hasClass('annotator-no-transition'))
        assert.equal(host.frame.css('pointer-events'), 'none')

      it 'captures the left margin as the gesture initial state', ->
        assert.equal(host.gestureState.initial, '100')

    describe 'panend event', ->
      it 'enables pointer events and transitions on the widget', ->
        host.gestureState = {final: 0}
        host.onPan({type: 'panend'})
        assert.isFalse(host.frame.hasClass('annotator-no-transition'))
        assert.equal(host.frame.css('pointer-events'), '')

      it 'calls `showFrame` if the widget is fully visible', ->
        host.gestureState = {final: -500}
        showFrame = sandbox.stub(host, 'showFrame')
        host.onPan({type: 'panend'})
        assert.calledOnce(showFrame)

      it 'calls `hideFrame` if the widget is not fully visible', ->
        host.gestureState = {final: -100}
        hideFrame = sandbox.stub(host, 'hideFrame')
        host.onPan({type: 'panend'})
        assert.calledOnce(hideFrame)

    describe 'panleft and panright events', ->
      raf = null

      # PhantomJS may or may not have rAF so the normal sandbox approach
      # doesn't quite work. We assign and delete it ourselves instead when
      # it isn't already present.
      beforeEach ->
        if window.requestAnimationFrame?
          sandbox.stub(window, 'requestAnimationFrame')
        else
          raf = window.requestAnimationFrame = sandbox.stub()

      afterEach ->
        if raf?
          raf = null
          delete window.requestAnimationFrame

      it 'shrinks or grows the widget to match the delta', ->
        host.gestureState = {initial: -100}

        host.onPan({type: 'panleft', deltaX: -50})
        assert.equal(host.gestureState.final, -150)

        host.onPan({type: 'panright', deltaX: 100})
        assert.equal(host.gestureState.final, 0)

  describe 'swipe gestures', ->
    host = null

    beforeEach ->
      host = createHost({})

    it 'opens the sidebar on swipeleft', ->
      showFrame = sandbox.stub(host, 'showFrame')
      host.onSwipe({type: 'swipeleft'})
      assert.calledOnce(showFrame)

    it 'closes the sidebar on swiperight', ->
      hideFrame = sandbox.stub(host, 'hideFrame')
      host.onSwipe({type: 'swiperight'})
      assert.calledOnce(hideFrame)
