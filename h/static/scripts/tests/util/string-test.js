import * as stringUtil from '../../util/string';

describe('util/string', () => {
  describe('hyphenate', () => {
    it('converts input to kebab-case', () => {
      assert.equal(stringUtil.hyphenate('fooBar'), 'foo-bar');
      assert.equal(stringUtil.hyphenate('FooBar'), '-foo-bar');
    });
  });

  describe('unhyphenate', () => {
    it('converts input to camelCase', () => {
      assert.equal(stringUtil.unhyphenate('foo-bar'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-'), 'fooBar');
      assert.equal(stringUtil.unhyphenate('foo-bar-baz'), 'fooBarBaz');
      assert.equal(stringUtil.unhyphenate('-foo-bar-baz'), 'FooBarBaz');
    });
  });

  describe('stringUtil helpers', () => {
    it('removes hungarian marks', () => {
      const text = 'Fürge rőt róka túlszökik zsíros étkű kutyán';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected = 'Furge rot roka tulszokik zsiros etku kutyan';

      assert.equal(decoded, expected);
    });

    it('removes greek marks', () => {
      const text = 'Καλημέρα κόσμε';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected = 'Καλημερα κοσμε';

      assert.equal(decoded, expected);
    });

    it('removes japanese marks', () => {
      const text = 'カタカナコンバータ';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected = 'カタカナコンハータ';

      assert.equal(decoded, expected);
    });

    it('removes marathi marks', () => {
      const text = 'काचं शक्नोम्यत्तुम';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected = 'कच शकनमयततम';

      assert.equal(decoded, expected);
    });

    it('removes thai marks', () => {
      const text = 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected = 'ฉนกนกระจกได แตมนไมทาใหฉนเจบ';

      assert.equal(decoded, expected);
    });

    it('removes all marks', () => {
      const text =
        '̀ ́ ̂ ̃ ̄ ̅ ̆ ̇ ̈ ̉ ̊ ̋ ̌ ̍ ̎ ̏ ̐ ̑ ̒ ̓ ̔ ̕ ̖ ̗ ̘ ̙ ̚ ̛ ̜ ̝ ̞ ̟ ̠ ̡ ̢ ̣ ̤ ̥ ̦ ̧ ̨ ̩ ̪ ̫ ̬ ̭ ̮ ̯ ̰ ̱ ̲ ̳ ̴ ̵ ̶ ̷ ̸ ̹ ̺ ̻ ̼ ̽ ̾ ̿ ̀ ́ ͂ ̓ ̈́ ͅ ͠ ͡"';
      const decoded = stringUtil.fold(stringUtil.normalize(text));
      const expected =
        '                                                                       "';

      assert.equal(decoded, expected);
    });
  });
});
