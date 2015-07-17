Annotator = require('annotator')
$ = Annotator.$

highlighter = require('../highlighter')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


describe "highlightRange", ->
  it 'wraps a highlight span around the given range', ->
    txt = document.createTextNode('test highlight span')
    el = document.createElement('span')
    el.appendChild(txt)
    r = new Annotator.Range.NormalizedRange({
      commonAncestor: el,
      start: txt,
      end: txt
    })
    result = highlighter.highlightRange(r)
    assert.equal(result.length, 1)
    assert.strictEqual(el.childNodes[0], result[0])
    assert.isTrue(result[0].classList.contains('annotator-hl'))

  it 'skips text nodes that are only white space', ->
    txt = document.createTextNode('one')
    blank = document.createTextNode(' ')
    txt2 = document.createTextNode('two')
    el = document.createElement('span')
    el.appendChild(txt)
    el.appendChild(blank)
    el.appendChild(txt2)
    r = new Annotator.Range.NormalizedRange({
      commonAncestor: el,
      start: txt,
      end: txt2
    })
    result = highlighter.highlightRange(r)
    assert.equal(result.length, 2)
    assert.strictEqual(el.childNodes[0], result[0])
    assert.strictEqual(el.childNodes[2], result[1])


describe 'removeHighlights', ->
  it 'unwraps all the elements', ->
    txt = document.createTextNode('word')
    el = document.createElement('span')
    hl = document.createElement('span')
    div = document.createElement('div')
    el.appendChild(txt)
    hl.appendChild(el)
    div.appendChild(hl)
    highlighter.removeHighlights([hl])
    assert.isNull(hl.parentNode)
    assert.strictEqual(el.parentNode, div)

  it 'does not fail on nodes with no parent', ->
    txt = document.createTextNode('no parent')
    hl = document.createElement('span')
    hl.appendChild(txt)
    highlighter.removeHighlights([hl])


describe "getBoundingClientRect", ->
  it 'returns the bounding box of all the highlight client rectangles', ->
    rects = [
      {
        top: 20
        left: 15
        bottom: 30
        right: 25
      }
      {
        top: 10
        left: 15
        bottom: 20
        right: 25
      }
      {
        top: 15
        left: 20
        bottom: 25
        right: 30
      }
      {
        top: 15
        left: 10
        bottom: 25
        right: 20
      }
    ]
    fakeHighlights = rects.map (r) ->
      return getBoundingClientRect: -> r
    result = highlighter.getBoundingClientRect(fakeHighlights)
    assert.equal(result.left, 10)
    assert.equal(result.top, 10)
    assert.equal(result.right, 30)
    assert.equal(result.bottom, 30)
