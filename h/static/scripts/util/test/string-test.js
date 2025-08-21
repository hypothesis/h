import { hyphenate, unhyphenate, stripMarks } from '../../util/string';

describe('util/string', () => {
  describe('hyphenate', () => {
    it('converts input to kebab-case', () => {
      assert.equal(hyphenate('fooBar'), 'foo-bar');
      assert.equal(hyphenate('FooBar'), '-foo-bar');
    });
  });

  describe('unhyphenate', () => {
    it('converts input to camelCase', () => {
      assert.equal(unhyphenate('foo-bar'), 'fooBar');
      assert.equal(unhyphenate('foo-bar-'), 'fooBar');
      assert.equal(unhyphenate('foo-bar-baz'), 'fooBarBaz');
      assert.equal(unhyphenate('-foo-bar-baz'), 'FooBarBaz');
    });
  });

  describe('stripAccents', () => {
    it('removes hungarian marks', () => {
      const text = 'Fürge rőt róka túlszökik zsíros étkű kutyán';
      const decoded = stripMarks(text);
      const expected = 'Furge rot roka tulszokik zsiros etku kutyan';

      assert.equal(decoded, expected);
    });

    it('removes greek marks', () => {
      const text = 'Καλημέρα κόσμε';
      const decoded = stripMarks(text);
      const expected = 'Καλημερα κοσμε';

      assert.equal(decoded, expected);
    });

    it('removes japanese marks', () => {
      const text = 'カタカナコンバータ';
      const decoded = stripMarks(text);
      const expected = 'カタカナコンハータ';

      assert.equal(decoded, expected);
    });

    it('removes marathi marks', () => {
      const text = 'काचं शक्नोम्यत्तुम';
      const decoded = stripMarks(text);
      const expected = 'कच शकनमयततम';

      assert.equal(decoded, expected);
    });

    it('removes thai marks', () => {
      const text = 'ฉันกินกระจกได้ แต่มันไม่ทำให้ฉันเจ็บ';
      const decoded = stripMarks(text);
      const expected = 'ฉนกนกระจกได แตมนไมทาใหฉนเจบ';

      assert.equal(decoded, expected);
    });

    it('removes all marks', () => {
      const text =
        '̀ ́ ̂ ̃ ̄ ̅ ̆ ̇ ̈ ̉ ̊ ̋ ̌ ̍ ̎ ̏ ̐ ̑ ̒ ̓ ̔ ̕ ̖ ̗ ̘ ̙ ̚ ̛ ̜ ̝ ̞ ̟ ̠ ̡ ̢ ̣ ̤ ̥ ̦ ̧ ̨ ̩ ̪ ̫ ̬ ̭ ̮ ̯ ̰ ̱ ̲ ̳ ̴ ̵ ̶ ̷ ̸ ̹ ̺ ̻ ̼ ̽ ̾ ̿ ̀ ́ ͂ ̓ ̈́ ͅ ͠ ͡"';
      const decoded = stripMarks(text);
      const expected =
        '                                                                       "';

      assert.equal(decoded, expected);
    });
  });
});
