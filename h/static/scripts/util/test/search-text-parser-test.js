import * as searchTextParser from '../../util/search-text-parser';

describe('SearchTextParser', () => {
  [
    { input: 'foo' },
    { input: '    foo    ' },
    { input: '"foo bar"' },
    { input: "'foo bar'" },
    { input: 'foo:"bar"' },
    { input: "foo:'bar'" },
    { input: "foo:'bar1 bar2'" },
    { input: 'foo:"bar1 bar2"' },
    { input: 'foo:' },
    { input: "'foo':" },
    { input: '"foo":' },
    { input: 'foo"bar:' },
    { input: "foo'bar:" },
    { input: "'foo'bar:" },
    { input: '"foo"bar:' },
    { input: "foo'bar" },
    { input: 'foo"bar' },
  ].forEach(fixture => {
    it('should create a lozenge #input', () => {
      assert.isTrue(searchTextParser.shouldLozengify(fixture.input));
    });
  });

  [
    { input: "foo'" },
    { input: 'foo"' },
    { input: "'foo" },
    { input: '"foo' },
    { input: '' },
    { input: "foo:'bar" },
    { input: 'foo:"bar' },
  ].forEach(fixture => {
    it('should not create a lozenge for', () => {
      assert.isFalse(searchTextParser.shouldLozengify(fixture.input));
    });
  });
});
