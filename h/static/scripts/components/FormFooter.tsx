import { Button } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';

export type FormFooterProps = {
  /** Whether to disable the submit button. */
  disableSubmit?: boolean;

  /** Label for the submit button. */
  submitLabel?: ComponentChildren;
};

/**
 * Form footer containing a submit button.
 */
export default function FormFooter({
  disableSubmit = false,
  submitLabel = 'Save',
}: FormFooterProps) {
  return (
    <div className="mb-4 pt-2 flex items-center gap-x-4">
      <div className="grow" />
      <Button
        type="submit"
        variant="primary"
        data-testid="submit-button"
        disabled={disableSubmit}
      >
        {submitLabel}
      </Button>
    </div>
  );
}
