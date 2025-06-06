import { formatDateTime, InfoIcon, Link } from '@hypothesis/frontend-shared';
import classnames from 'classnames';

import type {
  InvalidMentionContent,
  Mention,
  MentionMode,
} from '../helpers/mentions';

export type MentionPopoverContentProps = {
  content: Mention | InvalidMentionContent;
  mentionMode: MentionMode;
};

/**
 * Information to display in a Popover when hovering over a processed mention.
 */
export default function MentionPopoverContent({
  content,
  mentionMode,
}: MentionPopoverContentProps) {
  const isUsernameMode = mentionMode === 'username';

  return (
    <>
      <div className="px-3 py-2">
        {typeof content === 'string' ? (
          <div data-testid="user-not-found">
            No user with username <span className="font-bold">{content}</span>{' '}
            exists
          </div>
        ) : (
          <div className="flex flex-col gap-y-4">
            <div className="flex flex-col gap-y-1.5">
              {isUsernameMode && (
                <div data-testid="username" className="text-md font-bold">
                  @{content.username}
                </div>
              )}
              {content.display_name && (
                <div
                  data-testid="display-name"
                  className={classnames({
                    'text-color-text-light': isUsernameMode,
                    'text-md font-bold': !isUsernameMode,
                  })}
                >
                  {content.display_name}
                </div>
              )}
            </div>
            {content.description && (
              <div data-testid="description" className="line-clamp-2">
                {content.description}
              </div>
            )}
            {content.joined && (
              <div data-testid="joined" className="text-color-text-light">
                Joined{' '}
                <b>{formatDateTime(content.joined, { includeTime: false })}</b>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="px-3 py-2 border-t">
        <Link
          variant="text-light"
          classes="flex gap-x-1 items-center"
          target="_blank"
          href={
            isUsernameMode
              ? 'https://web.hypothes.is/help/mentions-for-the-hypothesis-web-app/'
              : 'https://web.hypothes.is/help/mentions-for-the-hypothesis-lms-app/'
          }
          data-testid="kb-article-link"
        >
          <InfoIcon className="w-3 h-3" /> Learn more about @mentions
        </Link>
      </div>
    </>
  );
}
