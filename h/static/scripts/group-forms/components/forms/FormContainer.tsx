import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type FormContainerProps = {
  title: string;
  children: ComponentChildren;
  classes?: string;
};

/** A container for a form with a title. */
export default function FormContainer({
  children,
  classes,
  title,
}: FormContainerProps) {
  return (
    <div className={classnames('text-grey-6 text-sm/relaxed', classes)}>
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none" data-testid="header">
        {title}
      </h1>
      {children}
    </div>
  );
}
