'use strict';

const searchTextParser = require('../../util/search-text-parser');
const unroll = require('../util').unroll;

describe('SearchTextParser', () => {
  unroll('should create a lozenge #input', (fixture) => {
    assert.isTrue(searchTextParser.shouldLozengify(fixture.input));
  },[
    {input: 'foo'},
    {input: '    foo    '},
    {input: '"foo bar"'},
    {input: '\'foo bar\''},
    {input: 'foo:"bar"'},
    {input: 'foo:\'bar\''},
    {input: 'foo:\'bar1 bar2\''},
    {input: 'foo:"bar1 bar2"'},
    {input: 'foo:'},
    {input: '\'foo\':'},
    {input: '"foo":'},
    {input: 'foo"bar:'},
    {input: 'foo\'bar:'},
    {input: '\'foo\'bar:'},
    {input: '"foo"bar:'},
    {input: 'foo\'bar'},
    {input: 'foo"bar'},
  ]);

  unroll('should not create a lozenge for', (fixture) => {
    assert.isFalse(searchTextParser.shouldLozengify(fixture.input));
  },[
    {input: 'foo\''},
    {input: 'foo\"'},
    {input: '\'foo'},
    {input: '\"foo'},
    {input: ''},
    {input: 'foo:\'bar'},
    {input: 'foo:\"bar'},
  ]);
});
