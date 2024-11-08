import type { ComponentChildren } from 'preact';

export type FormContainerProps = {
  title: string;
  children: ComponentChildren;
};

/** A container for a form with a title. */
export default function FormContainer({ children, title }: FormContainerProps) {
  return (
    <div className="text-grey-6 text-sm/relaxed">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none" data-testid="header">
        {title}
      </h1>
      {children}
    </div>
  );
}
