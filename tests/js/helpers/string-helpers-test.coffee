assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'h.helpers.stringHelpers', ->
  stringHelpers = null

  beforeEach module('h.helpers')

  beforeEach inject (_stringHelpers_) ->
    stringHelpers = _stringHelpers_

  describe '.uniFold', ->
    it 'normalizes the input string', ->
      text = 'die Stra\u00DFe'
      decoded = stringHelpers.uniFold text

      assert.equal decoded, 'die Straße'

    it 'calls the right normalization', ->
      stub = sinon.stub(unorm, "nfkd").returns('')
      stringHelpers.uniFold ''

      sinon.assert.called unorm.nfkd
      stub.restore()

    it 'removes combining characters', ->
      text = 'Fürge rőt róka túlszökik zsíros étkű kutyán'
      decoded = stringHelpers.uniFold text
      expected = 'Furge rot roka tulszokik zsiros etku kutyan'

      assert.equal decoded, expected
