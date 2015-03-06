{module, inject} = require('angular-mock')

assert = chai.assert
sinon.assert.expose(assert, prefix: '')


describe 'h.helpers:string-helpers', ->
  stringHelpers = null

  before ->
    angular.module('h.helpers', [])
    require('../string-helpers')

  beforeEach module('h.helpers')

  beforeEach inject (_stringHelpers_) ->
    stringHelpers = _stringHelpers_

  describe '.uniFold', ->
    it 'removes hungarian marks', ->
      text = 'Fürge rőt róka túlszökik zsíros étkű kutyán'
      decoded = stringHelpers.uniFold text
      expected = 'Furge rot roka tulszokik zsiros etku kutyan'

      assert.equal decoded, expected

    it 'removes greek marks', ->
      text = 'Καλημέρα κόσμε'
      decoded = stringHelpers.uniFold text
      expected = 'Καλημερα κοσμε'

      assert.equal decoded, expected

    it 'removes japanese marks', ->
      text = 'カタカナコンバータ'
      decoded = stringHelpers.uniFold text
      expected = 'カタカナコンハータ'

      assert.equal decoded, expected

    it 'removes marathi marks', ->
      text = 'काचं शक्नोम्यत्तुम'
      decoded = stringHelpers.uniFold text
      expected = 'कच शकनमयततम'

      assert.equal decoded, expected

    it 'removes thai marks', ->
      text = 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ'
      decoded = stringHelpers.uniFold text
      expected = 'ฉนกนกระจกได แตมนไมทาใหฉนเจบ'

      assert.equal decoded, expected

    it 'removes all marks', ->
      text = '̀ ́ ̂ ̃ ̄ ̅ ̆ ̇ ̈ ̉ ̊ ̋ ̌ ̍ ̎ ̏ ̐ ̑ ̒ ̓ ̔ ̕ ̖ ̗ ̘ ̙ ̚ ̛ ̜ ̝ ̞ ̟ ̠ ̡ ̢ ̣ ̤ ̥ ̦ ̧ ̨ ̩ ̪ ̫ ̬ ̭ ̮ ̯ ̰ ̱ ̲ ̳ ̴ ̵ ̶ ̷ ̸ ̹ ̺ ̻ ̼ ̽ ̾ ̿ ̀ ́ ͂ ̓ ̈́ ͅ ͠ ͡"'
      decoded = stringHelpers.uniFold text
      expected = '                                                                       "'

      assert.equal decoded, expected
