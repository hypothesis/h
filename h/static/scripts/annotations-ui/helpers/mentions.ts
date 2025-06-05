/** A date and time in ISO format (eg. "2024-12-09T07:17:52+00:00") */
export type ISODateTime = string;

/**
 * The content of a mention tag that the backend "discarded" as invalid.
 * Possible reasons are: the user does not exist, belongs to a different group,
 * is nipsa'd, etc.
 */
export type InvalidMentionContent = string;

/**
 * Whether mentions should be done via username (`@username`) or display name
 * (`@[Display Name]`).
 *
 * This also affects the information displayed in suggestions, which will not
 * include the username in the second case.
 */
export type MentionMode = 'username' | 'display-name';

export type Mention = {
  /** Current userid for the user that was mentioned */
  userid: string;
  /** Current username for the user that was mentioned */
  username: string;
  /** Current display name for the user that was mentioned */
  display_name: string | null;
  /** Link to the user profile, if applicable */
  link: string | null;
  /** The user description/bio */
  description: string | null;
  /** The date when the user joined, in ISO format */
  joined: ISODateTime | null;

  /**
   * The userid at the moment the mention was created.
   * If the user changes their username later, this can be used to match the
   * right mention tag in the annotation text.
   */
  original_userid: string;
};

/**
 * Replace an unprocessed mention tag with another element that represents the
 * proper type of mention ('link', 'no-link' or 'invalid').
 */
function processAndReplaceMention(
  unprocessedMention: HTMLElement,
  mention: Mention | undefined,
  mentionMode: MentionMode,
): [HTMLElement, Mention | InvalidMentionContent] {
  const originalTagContent = unprocessedMention.textContent ?? '';
  const mentionOrInvalidContent = mention ?? originalTagContent;

  // If this mention element has already been processed, return as is
  if (unprocessedMention.hasAttribute('data-hyp-mention-type')) {
    return [unprocessedMention, mentionOrInvalidContent];
  }

  const type =
    mention && mention.link ? 'link' : mention ? 'no-link' : 'invalid';
  const processedMention = document.createElement(
    type === 'link' ? 'a' : 'span',
  );

  processedMention.setAttribute('data-hyp-mention', '');
  processedMention.setAttribute('data-hyp-mention-type', type);

  // For valid mentions, resolve the most recent username or display name, in
  // case it has changed since the mention was created.
  // The only exception is when a valid mention with an empty display name is
  // resolved, in which case we fall back to the original tag content.
  if (!mention) {
    processedMention.textContent = originalTagContent;
  } else if (mentionMode === 'username') {
    processedMention.textContent = `@${mention.username}`;
  } else {
    processedMention.textContent = mention.display_name
      ? `@${mention.display_name}`
      : originalTagContent;
  }

  if (type === 'link') {
    // If the mention exists in the list of mentions and contains a link, render
    // it as an anchor pointing to that link
    processedMention.setAttribute('href', mention?.link ?? '');
    processedMention.setAttribute('target', '_blank');
  }

  if (type !== 'invalid') {
    processedMention.setAttribute(
      'data-userid',
      unprocessedMention.dataset.userid ?? '',
    );
  }

  unprocessedMention.replaceWith(processedMention);
  return [processedMention, mentionOrInvalidContent];
}

/**
 * Search for mention tags inside an HTML element, and try to match them with a
 * provided list of mentions. Every matched element will be replaced with
 * another one that represents the proper type of mention ('link', 'no-link' or
 * 'invalid').
 *
 * @return - Map of HTML elements that matched a mention tag, with their
 *           corresponding mention or invalid username
 */
export function processAndReplaceMentionElements(
  element: HTMLElement,
  mentions: Mention[],
  mentionMode: MentionMode,
): Map<HTMLElement, Mention | InvalidMentionContent> {
  const mentionElements = element.querySelectorAll('[data-hyp-mention]');
  const foundMentions = new Map<HTMLElement, Mention | string>();

  for (const mentionElement of mentionElements) {
    const htmlMentionElement = mentionElement as HTMLElement;
    const mentionUserId = htmlMentionElement.dataset.userid;
    const mention = mentionUserId
      ? mentions.find(m => m.userid === mentionUserId)
      : undefined;

    foundMentions.set(
      ...processAndReplaceMention(htmlMentionElement, mention, mentionMode),
    );
  }

  return foundMentions;
}
