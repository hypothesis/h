assert = chai.assert
sinon.assert.expose(assert, prefix: '')

describe 'h.helpers.stringHelpers', ->
  stringHelpers = null

  beforeEach module('h.helpers.stringHelpers')

  beforeEach inject (_stringHelpers_) ->
    stringHelpers = _stringHelpers_

  describe '.unidecode', ->
    it 'normalizes the input string', ->
      text = 'die Stra\u00DFe'
      decoded = stringHelpers.unidecode text

      assert.equal decoded, 'die Straße'

    it 'calls the right normalization', ->
      unorm.nfc = sinon.stub().returns('')
      stringHelpers.unidecode '', 'nfc'

      sinon.assert.called unorm.nfc

    it 'removes combining characters', ->
      text = 'Fürge rőt róka túlszökik zsíros étkű kutyán'
      decoded = stringHelpers.unidecode text
      expected = 'Furge rot roka tulszokik zsiros etku kutyan'

      assert.equal decoded, expected
