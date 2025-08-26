import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { Link as RouterLink, useRoute } from 'wouter-preact';

export type TabLinkProps = {
  href: string;
  children: ComponentChildren;
  testId?: string;

  /**
   * If true, use a server-side navigation for this link.
   *
   * Defaults to false.
   */
  server?: boolean;
};

function TabLink({ children, href, testId, server = false }: TabLinkProps) {
  const [selected] = useRoute(href);
  const Component = server ? 'a' : RouterLink;

  return (
    <Component
      href={href}
      className={classnames({
        'focus-visible-ring whitespace-nowrap flex items-center font-semibold rounded px-2 py-1 gap-x-2':
          true,
        'text-grey-1 bg-grey-7': selected,
      })}
      data-testid={testId}
      aria-current={selected}
      role="listitem"
    >
      {children}
    </Component>
  );
}

export type TabLinksProps = {
  children: ComponentChildren;
};

/**
 * A list of navigation links styled as tabs.
 *
 * Individual links are created using {@link TabLinks.Link}. The tab which
 * corresponds to the current route is displayed as selected.
 */
export default function TabLinks({ children }: TabLinksProps) {
  return (
    <div role="list" className="flex gap-x-2">
      {children}
    </div>
  );
}

TabLinks.Link = TabLink;
