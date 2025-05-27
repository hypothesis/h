import type { ComponentChildren } from 'preact';

export type TagListProps = {
  children: ComponentChildren;
};

/**
 * Render a list container for a list of annotation tags.
 */
export default function TagList({ children }: TagListProps) {
  return (
    <ul
      className="flex flex-wrap gap-2 leading-none"
      aria-label="Annotation tags"
    >
      {children}
    </ul>
  );
}
