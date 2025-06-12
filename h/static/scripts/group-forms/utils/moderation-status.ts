import type { ModerationStatus } from './api';

export const moderationStatusToLabel: Record<ModerationStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  DENIED: 'Denied',
  SPAM: 'Spam',
} as const;

Object.freeze(moderationStatusToLabel);
