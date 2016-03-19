'use strict';

var commands = require('../markdown-commands');

/**
 * Convert a string containing '<sel>' and '</sel>' markers
 * to a commands.EditorState.
 */
function parseState(text) {
  var startMarker = '<sel>';
  var endMarker = '</sel>';

  var selStart = text.indexOf(startMarker);
  var selEnd = text.indexOf(endMarker);

  if (selStart < 0) {
    throw new Error('Input field does not contain a selection start');
  }
  if (selEnd < 0) {
    throw new Error('Input field does not contain a selection end');
  }

  return {
    text: text.replace(/<\/?sel>/g, ''),
    selectionStart: selStart,
    selectionEnd: selEnd - startMarker.length,
  };
}

/**
 * Convert a commands.EditorState to a string containing '<sel>'
 * and '</sel>' markers.
 */
function formatState(state) {
  var selectionStart = state.selectionStart;
  var selectionEnd = state.selectionEnd;
  var text = state.text;
  return text.slice(0, selectionStart) + '<sel>' +
         text.slice(selectionStart, selectionEnd) + '</sel>' +
         text.slice(selectionEnd);
}

describe('markdown commands', function () {
  describe('span formatting', function () {
    function toggle(state, prefix, suffix, placeholder) {
      prefix = prefix || '**';
      suffix = suffix || '**';
      return commands.toggleSpanStyle(state, prefix, suffix, placeholder);
    }

    it('adds formatting to spans', function () {
      var output = toggle(parseState('make <sel>text</sel> bold'));
      assert.equal(formatState(output), 'make **<sel>text</sel>** bold');
    });

    it('removes formatting from spans', function () {
      var output = toggle(parseState('make **<sel>text</sel>** bold'));
      assert.equal(formatState(output), 'make <sel>text</sel> bold');
    });

    it('adds formatting to spans when the prefix and suffix differ', function () {
      var output = toggle(parseState('make <sel>math</sel> mathy'), '\\(',
                                     '\\)');
      assert.equal(formatState(output), 'make \\(<sel>math</sel>\\) mathy');
    });

    it('inserts placeholders if the selection is empty', function () {
      var output = toggle(parseState('make <sel></sel> bold'), '**',
                          undefined, 'Bold');
      assert.equal(formatState(output), 'make **<sel>Bold</sel>** bold');
    });
  });

  describe('block formatting', function () {
    var CASES = {
      'adds formatting to blocks': {
        input: 'one\n<sel>two\nthree</sel>\nfour',
        output: 'one\n> <sel>two\n> three</sel>\nfour',
      },
      'removes formatting from blocks': {
        input: 'one \n<sel>> two\n> three</sel>\nfour',
        output: 'one \n<sel>two\nthree</sel>\nfour',
      },
      'preserves the selection': {
        input: 'one <sel>two\nthree </sel>four',
        output: '> one <sel>two\n> three </sel>four',
      }
    };

    Object.keys(CASES).forEach(function (case_) {
      it(case_, function () {
        var output = commands.toggleBlockStyle(
          parseState(CASES[case_].input), '> '
        );
        assert.equal(formatState(output), CASES[case_].output);
      });
    });
  });

  describe('link formatting', function () {
    var linkify = function (text, linkType) {
      return commands.convertSelectionToLink(parseState(text), linkType);
    };

    it('converts text to links', function () {
      var output = linkify('one <sel>two</sel> three');
      assert.equal(formatState(output),
        'one [two](<sel>http://insert-your-link-here.com</sel>) three');
    });

    it('converts URLs to links', function () {
      var output = linkify('one <sel>http://foobar.com</sel> three');
      assert.equal(formatState(output),
        'one [<sel>Description</sel>](http://foobar.com) three');
    });

    it('converts URLs to image links', function () {
      var output = linkify('one <sel>http://foobar.com</sel> three',
        commands.LinkType.IMAGE_LINK);
      assert.equal(formatState(output),
        'one ![<sel>Description</sel>](http://foobar.com) three');
    });
  });
});
