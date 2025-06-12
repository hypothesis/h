import { pageLabel, quote, username } from '../annotation-metadata';

describe('quote', () => {
  it('returns quote if annotation has a quote', () => {
    const ann = {
      target: [
        {
          source: 'https://publisher.org/article.pdf',
          selector: [{ type: 'TextQuoteSelector', exact: 'expected quote' }],
        },
      ],
    };
    assert.equal(quote(ann), 'expected quote');
  });

  // FIXME - This currently happens when creating a new Page Note. Annotations
  // from the API should always have a target.
  //
  // See https://github.com/hypothesis/client/issues/1290.
  it('returns `null` if annotation has an empty target array', () => {
    const ann = { target: [] };
    assert.equal(quote(ann), null);
  });

  it('returns `null` if annotation has no selectors', () => {
    const ann = {
      target: [
        {
          source: 'https://publisher.org/article.pdf',
        },
      ],
    };
    assert.equal(quote(ann), null);
  });

  it('returns `null` if annotation has no text quote selector', () => {
    const ann = {
      target: [
        {
          source: 'https://publisher.org/article.pdf',
          selector: [{ type: 'TextPositionSelector', start: 0, end: 100 }],
        },
      ],
    };
    assert.equal(quote(ann), null);
  });
});

describe('pageLabel', () => {
  it('returns page label for annotation', () => {
    const ann = {
      target: [
        {
          source: 'https://publisher.org/article.pdf',
          selector: [{ type: 'PageSelector', index: 10, label: '11' }],
        },
      ],
    };
    assert.equal(pageLabel(ann), '11');
  });

  it('returns undefined if annotation has no `PageSelector` selector', () => {
    const pageNote = {
      $highlight: undefined,
      target: [{ source: 'http://example.org' }],
      references: [],
      text: '',
      tags: [],
    };
    const newAnno = {
      id: undefined,
      $highlight: undefined,
      target: ['foo', 'bar'],
      references: [],
      text: 'Annotation text',
      tags: ['tag_1', 'tag_2'],
      user: 'acct:bill@localhost',
    };
    const anns = [pageNote, newAnno];

    for (const ann of anns) {
      assert.isUndefined(pageLabel(ann));
    }
  });
});

describe('username', () => {
  const term = 'acct:hacker@example.com';

  it('should return the username from the account ID', () => {
    assert.equal(username(term), 'hacker');
  });

  it('should return undefined if the ID is invalid', () => {
    assert.isUndefined(username('bogus'));
  });

  it('should return undefined if the account ID is null', () => {
    assert.isUndefined(username(null));
  });
});
