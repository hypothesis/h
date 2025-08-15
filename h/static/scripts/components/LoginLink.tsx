import { ArrowRightIcon, ExternalIcon } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { Link as RouterLink } from 'wouter-preact';

export type LoginLinkProps = {
  /** True if this navigation is handled client-side. */
  routerLink?: boolean;

  /** Target URL for the link. */
  href: string;

  /** Icon for the identity provider. */
  providerIcon: ComponentChildren;

  /** Text for the link (eg. "Continue with Google"). */
  children: ComponentChildren;
};

/**
 * Base component for login / sign-up provider buttons.
 */
export default function LoginLink({
  routerLink,
  href,
  providerIcon,
  children,
}: LoginLinkProps) {
  const LinkType = routerLink ? RouterLink : 'a';
  const NavigateIcon = routerLink ? ArrowRightIcon : ExternalIcon;

  return (
    <LinkType
      href={href}
      className="border rounded-md p-3 flex flex-row items-center gap-x-3"
    >
      {providerIcon}
      <span className="grow">{children}</span>
      <NavigateIcon className="w-[20px] h-[20px]" />
    </LinkType>
  );
}
