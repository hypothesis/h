import type { JSX } from 'preact';

export default function Text({
  children,
  ...rest
}: JSX.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className="my-2" {...rest}>
      {children}
    </p>
  );
}
