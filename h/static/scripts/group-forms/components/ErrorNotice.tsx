import { CancelIcon } from '@hypothesis/frontend-shared';

export type ErrorNoticeProps = {
  message: string | null;
};

/**
 * A live region which displays an error message.
 *
 * If there is no error, the container should be rendered with a null `message`.
 * This will cause any error message that is displayed later to be announced
 * to screen readers.
 */
export default function ErrorNotice({ message }: ErrorNoticeProps) {
  return (
    <div data-testid="error-container" role="alert">
      {message && (
        <div
          className="text-red-error font-bold flex items-center gap-x-2"
          data-testid="error-message"
        >
          <CancelIcon />
          {message}
        </div>
      )}
    </div>
  );
}
