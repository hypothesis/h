import { processAndReplaceMentionElements } from '../mentions';

/**
 * @param {string} username
 * @param {string} [authority] - Defaults to 'hypothes.is'
 * @param {string} [content] - Defaults to `@${username}`
 * @param {'link'|'no-link'|'invalid'} [type]
 * @returns {HTMLAnchorElement}
 */
function mentionElement({
  username,
  authority = 'hypothes.is',
  content = `@${username}`,
  type,
}) {
  const element = document.createElement('a');

  element.setAttribute('data-hyp-mention', '');
  element.setAttribute('data-userid', `acct:${username}@${authority}`);

  if (type) {
    element.setAttribute('data-hyp-mention-type', type);
  }

  element.textContent = content;

  return element;
}

const mentionTag = (username, authority) =>
  mentionElement({ username, authority }).outerHTML;

describe('processAndReplaceMentionElements', () => {
  it('processes every mention tag based on provided list of mentions', () => {
    const mentions = [
      {
        userid: 'acct:janedoe@hypothes.is',
        link: 'http://example.com/janedoe',
      },
      {
        userid: 'acct:johndoe@hypothes.is',
        link: null,
      },
    ];

    const container = document.createElement('div');
    container.innerHTML = `
      <p>Correct mention: ${mentionTag('janedoe', 'hypothes.is')}</p>
      <p>Non-link mention: ${mentionTag('johndoe', 'hypothes.is')}</p>
      <p>Invalid mention: ${mentionTag('invalid', 'hypothes.is')}</p>
      <p>Mention without ID: <a data-hyp-mention="">@user_id_missing</a></p>
    `;

    const result = processAndReplaceMentionElements(
      container,
      mentions,
      'username',
    );
    assert.equal(result.size, 4);

    const [
      [firstElement, firstMention],
      [secondElement, secondMention],
      [thirdElement, thirdMention],
      [fourthElement, fourthMention],
    ] = [...result.entries()];

    // First element will render as an actual anchor with href
    assert.equal(firstElement.tagName, 'A');
    assert.equal(
      firstElement.getAttribute('href'),
      'http://example.com/janedoe',
    );
    assert.equal(firstElement.dataset.hypMentionType, 'link');
    assert.equal(firstMention, mentions[0]);

    // Second element will render as a highlighted span
    assert.equal(secondElement.tagName, 'SPAN');
    assert.equal(secondElement.dataset.userid, 'acct:johndoe@hypothes.is');
    assert.equal(secondElement.dataset.hypMentionType, 'no-link');
    assert.isTrue(secondElement.hasAttribute('data-userid'));
    assert.equal(secondMention, mentions[1]);

    // Third and fourth elements will be invalid mentions wrapping the invalid
    // username
    assert.equal(thirdElement.tagName, 'SPAN');
    assert.isFalse(thirdElement.hasAttribute('data-userid'));
    assert.equal(thirdElement.dataset.hypMentionType, 'invalid');
    assert.equal(thirdMention, '@invalid');
    assert.equal(fourthElement.tagName, 'SPAN');
    assert.isFalse(fourthElement.hasAttribute('data-userid'));
    assert.equal(fourthElement.dataset.hypMentionType, 'invalid');
    assert.equal(fourthMention, '@user_id_missing');
  });

  it('returns already-processed mention elements unchanged', () => {
    const mentions = [
      {
        userid: 'acct:janedoe@hypothes.is',
        link: 'http://example.com/janedoe',
      },
      {
        userid: 'acct:johndoe@hypothes.is',
        link: null,
      },
    ];

    const container = document.createElement('div');
    const correctProcessedMention = mentionElement({
      username: 'janedoe',
      type: 'link',
    });
    const nonLinkProcessedMention = mentionElement({
      username: 'johndoe',
      type: 'no-link',
    });
    const invalidProcessedMention = mentionElement({
      username: 'invalid',
      type: 'invalid',
    });

    container.append(
      correctProcessedMention,
      nonLinkProcessedMention,
      invalidProcessedMention,
    );

    const result = processAndReplaceMentionElements(
      container,
      mentions,
      'username',
    );
    assert.equal(result.size, 3);

    const [
      [firstElement, firstMention],
      [secondElement, secondMention],
      [thirdElement, thirdMention],
    ] = [...result.entries()];

    assert.equal(firstElement, correctProcessedMention);
    assert.equal(firstMention, mentions[0]);

    assert.equal(secondElement, nonLinkProcessedMention);
    assert.equal(secondMention, mentions[1]);

    assert.equal(thirdElement, invalidProcessedMention);
    assert.equal(thirdMention, '@invalid');
  });

  [
    {
      mentionMode: 'username',
      oldContent: '@janedoe',
      mention: { username: 'janedoe_updated' },
      expectedContent: '@janedoe_updated',
    },
    {
      mentionMode: 'display-name',
      oldContent: '@Jane Doe',
      mention: { display_name: 'Jane Doe Updated' },
      expectedContent: '@Jane Doe Updated',
    },
    {
      mentionMode: 'display-name',
      oldContent: '@Jane Doe',
      mention: { display_name: '' },
      expectedContent: '@Jane Doe',
    },
  ].forEach(({ mentionMode, oldContent, mention, expectedContent }) => {
    it('returns most recent usernames or display names', () => {
      const mentions = [
        {
          userid: 'acct:janedoe@hypothes.is',
          ...mention,
        },
      ];
      const container = document.createElement('div');
      container.innerHTML = mentionElement({
        username: 'janedoe',
        content: oldContent,
      }).outerHTML;

      const result = processAndReplaceMentionElements(
        container,
        mentions,
        mentionMode,
      );
      const [[mentionEl]] = [...result.entries()];

      assert.equal(mentionEl.textContent, expectedContent);
    });
  });
});
