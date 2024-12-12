import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type FormContainerProps = {
  children: ComponentChildren;
  classes?: string;
};

/** A container for a form with a title. */
export default function FormContainer({
  children,
  classes,
}: FormContainerProps) {
  return (
    <div className={classnames('text-grey-6 text-sm/relaxed', classes)}>
      {children}
    </div>
  );
}
