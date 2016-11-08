'use strict';

var stringUtil = require('../../util/string');

describe('util/string', function () {
  describe('hyphenate', function () {
    it('converts input to kebab-case', function () {
      assert.equal(stringUtil.hyphenate('fooBar'), 'foo-bar');
      assert.equal(stringUtil.hyphenate('FooBar'), '-foo-bar');
    });
  });

  describe('unhyphenate', function () {
    it('converts input to camelCase', function () {
      assert.equal(stringUtil.unhyphenate('foo-bar'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-baz'), 'fooBarBaz');
      assert.equal(stringUtil.unhyphenate('-foo-bar-baz'), 'FooBarBaz');
    });
  });

  describe('stringUtil helpers', function(){

    it('removes hungarian marks', function(){
      let text = 'Fürge rőt róka túlszökik zsíros étkű kutyán';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = 'Furge rot roka tulszokik zsiros etku kutyan';

      assert.equal(decoded, expected);
    });

    it('removes greek marks', function(){
      let text = 'Καλημέρα κόσμε';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = 'Καλημερα κοσμε';

      assert.equal(decoded, expected);
    });

    it('removes japanese marks', function(){
      let text = 'カタカナコンバータ';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = 'カタカナコンハータ';

      assert.equal(decoded, expected);
    });

    it('removes marathi marks', function(){
      let text = 'काचं शक्नोम्यत्तुम';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = 'कच शकनमयततम';

      assert.equal(decoded, expected);
    });

    it('removes thai marks', function(){
      let text = 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = 'ฉนกนกระจกได แตมนไมทาใหฉนเจบ';

      assert.equal(decoded, expected);
    });

    it('removes all marks', function(){
      let text = '̀ ́ ̂ ̃ ̄ ̅ ̆ ̇ ̈ ̉ ̊ ̋ ̌ ̍ ̎ ̏ ̐ ̑ ̒ ̓ ̔ ̕ ̖ ̗ ̘ ̙ ̚ ̛ ̜ ̝ ̞ ̟ ̠ ̡ ̢ ̣ ̤ ̥ ̦ ̧ ̨ ̩ ̪ ̫ ̬ ̭ ̮ ̯ ̰ ̱ ̲ ̳ ̴ ̵ ̶ ̷ ̸ ̹ ̺ ̻ ̼ ̽ ̾ ̿ ̀ ́ ͂ ̓ ̈́ ͅ ͠ ͡"';
      let decoded = stringUtil.fold(stringUtil.normalize(text));
      let expected = '                                                                       "';

      assert.equal(decoded, expected);
    });

  });
});
