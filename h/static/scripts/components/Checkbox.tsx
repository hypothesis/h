import type { CheckboxProps as BaseCheckboxProps } from '@hypothesis/frontend-shared';
import { Checkbox as BaseCheckbox } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useId } from 'preact/hooks';

import ErrorNotice from './ErrorNotice';

export type CheckboxProps = Omit<BaseCheckboxProps, 'aria-describedby'> & {
  /**
   * Adds a description right under the checkbox and main content, aligned with
   * the main content's left side.
   */
  description?: ComponentChildren;
  /** Optional error message for the checkbox. */
  error?: string;
};

/**
 * Render a labeled checkbox input, with an optional description underneath.
 */
export default function Checkbox({
  description,
  children,
  error = '',
  ...checkboxProps
}: CheckboxProps) {
  const descriptionId = useId();

  return (
    <div>
      <BaseCheckbox
        {...checkboxProps}
        aria-describedby={description ? descriptionId : undefined}
      >
        {children}
      </BaseCheckbox>
      {description && (
        <div
          data-testid="description"
          id={descriptionId}
          className="text-grey-6 mt-1 ml-5"
        >
          {description}
        </div>
      )}
      {error && (
        <div className="mt-1">
          <ErrorNotice message={error} />
        </div>
      )}
    </div>
  );
}
