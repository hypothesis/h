{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


describe 'unicode', ->
  unicode = null

  before ->
    angular.module('h', []).service('unicode', require('../unicode'))

  beforeEach module('h')
  beforeEach inject (_unicode_) ->
    unicode = _unicode_

  describe '.fold', ->
    it 'removes hungarian marks', ->
      text = 'Fürge rőt róka túlszökik zsíros étkű kutyán'
      decoded = unicode.fold(unicode.normalize(text))
      expected = 'Furge rot roka tulszokik zsiros etku kutyan'

      assert.equal decoded, expected

    it 'removes greek marks', ->
      text = 'Καλημέρα κόσμε'
      decoded = unicode.fold(unicode.normalize(text))
      expected = 'Καλημερα κοσμε'

      assert.equal decoded, expected

    it 'removes japanese marks', ->
      text = 'カタカナコンバータ'
      decoded = unicode.fold(unicode.normalize(text))
      expected = 'カタカナコンハータ'

      assert.equal decoded, expected

    it 'removes marathi marks', ->
      text = 'काचं शक्नोम्यत्तुम'
      decoded = unicode.fold(unicode.normalize(text))
      expected = 'कच शकनमयततम'

      assert.equal decoded, expected

    it 'removes thai marks', ->
      text = 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ'
      decoded = unicode.fold(unicode.normalize(text))
      expected = 'ฉนกนกระจกได แตมนไมทาใหฉนเจบ'

      assert.equal decoded, expected

    it 'removes all marks', ->
      text = '̀ ́ ̂ ̃ ̄ ̅ ̆ ̇ ̈ ̉ ̊ ̋ ̌ ̍ ̎ ̏ ̐ ̑ ̒ ̓ ̔ ̕ ̖ ̗ ̘ ̙ ̚ ̛ ̜ ̝ ̞ ̟ ̠ ̡ ̢ ̣ ̤ ̥ ̦ ̧ ̨ ̩ ̪ ̫ ̬ ̭ ̮ ̯ ̰ ̱ ̲ ̳ ̴ ̵ ̶ ̷ ̸ ̹ ̺ ̻ ̼ ̽ ̾ ̿ ̀ ́ ͂ ̓ ̈́ ͅ ͠ ͡"'
      decoded = unicode.fold(unicode.normalize(text))
      expected = '                                                                       "'

      assert.equal decoded, expected
