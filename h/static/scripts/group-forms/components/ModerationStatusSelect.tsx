import type { IconComponent } from '@hypothesis/frontend-shared';
import {
  FilterIcon,
  CautionIcon,
  RestrictedIcon,
  CheckAllIcon,
  DottedCircleIcon,
  Select,
} from '@hypothesis/frontend-shared';

import type { ModerationStatus } from '../utils/api';
import { moderationStatusToLabel } from '../utils/moderation-status';

export type ModerationStatusSelectProps = {
  selected?: ModerationStatus;
  onChange: (status?: ModerationStatus) => void;
};

type Option = {
  icon: IconComponent;
  label: string;
};

const options = new Map<ModerationStatus, Option>([
  [
    'PENDING',
    { label: moderationStatusToLabel.PENDING, icon: DottedCircleIcon },
  ],
  ['APPROVED', { label: moderationStatusToLabel.APPROVED, icon: CheckAllIcon }],
  ['DENIED', { label: moderationStatusToLabel.DENIED, icon: RestrictedIcon }],
  ['SPAM', { label: moderationStatusToLabel.SPAM, icon: CautionIcon }],
]);

export default function ModerationStatusSelect({
  selected,
  onChange,
}: ModerationStatusSelectProps) {
  const selectedName = selected ? options.get(selected)?.label : undefined;

  return (
    <Select
      value={selected}
      onChange={onChange}
      alignListbox="right"
      containerClasses="!w-auto"
      aria-label="Moderation status"
      buttonContent={
        <div className="flex gap-x-1.5 items-center">
          <FilterIcon />
          {selectedName ?? 'All'}
        </div>
      }
    >
      <Select.Option value={undefined} classes="text-grey-7">
        All
      </Select.Option>
      {[...options.entries()].map(([status, { label, icon: Icon }]) => (
        <Select.Option key={status} value={status}>
          <div className="flex gap-x-1.5 items-center text-grey-7">
            <Icon />
            {label}
          </div>
        </Select.Option>
      ))}
    </Select>
  );
}
