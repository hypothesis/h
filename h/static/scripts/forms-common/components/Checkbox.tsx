import type { CheckboxProps as BaseCheckboxProps } from '@hypothesis/frontend-shared';
import { Checkbox as BaseCheckbox } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useId } from 'preact/hooks';

export type CheckboxProps = Omit<BaseCheckboxProps, 'aria-describedby'> & {
  /**
   * Adds a description right under the checkbox and main content, aligned with
   * the main content's left side.
   */
  description?: ComponentChildren;
};

/**
 * Render a labeled checkbox input, with an optional description underneath.
 */
export default function Checkbox({
  description,
  children,
  ...checkboxProps
}: CheckboxProps) {
  const descriptionId = useId();

  return (
    <div>
      <BaseCheckbox
        {...checkboxProps}
        aria-describedby={description ? descriptionId : undefined}
      >
        <span className="text-grey-7">{children}</span>
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
    </div>
  );
}
