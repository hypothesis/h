import type { IconComponent } from '@hypothesis/frontend-shared';
import {
  FilterIcon,
  CautionIcon,
  RestrictedIcon,
  CheckAllIcon,
  DottedCircleIcon,
  Select,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { Fragment } from 'preact';

import type { ModerationStatus } from '../utils/api';
import { moderationStatusToLabel } from '../utils/moderation-status';

export type ModerationStatusSelectProps = {
  alignListbox?: 'right' | 'left';
  disabled?: boolean;
} & (
  | {
      /** This select is used to filter a list of annotations by moderation status */
      mode: 'filter';
      selected?: ModerationStatus;
      onChange: (status?: ModerationStatus) => void;
    }
  | {
      /** This select is used to set the moderation status of a specific annotation */
      mode: 'select';
      selected: ModerationStatus;
      onChange: (status: ModerationStatus) => void;
    }
);

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
  mode,
  alignListbox = 'right',
  disabled,
}: ModerationStatusSelectProps) {
  const selectedName = selected ? options.get(selected)!.label : undefined;
  const SelectedIcon = selected ? options.get(selected)!.icon : Fragment;

  return (
    <Select
      value={selected}
      // Cast to bypass TS warning that callback does not accept `undefined`.
      // We will only include `undefined` in the options if `mode == "filter"`
      // and this is allowed.
      onChange={onChange as (value: ModerationStatus | undefined) => void}
      alignListbox={alignListbox}
      containerClasses="!w-auto"
      buttonClasses={classnames(
        mode === 'select' && {
          '!bg-green-light !text-green-dark': selected === 'APPROVED',
          '!bg-yellow-light !text-yellow-dark': selected === 'SPAM',
          '!bg-red-light !text-red-dark': selected === 'DENIED',
        },
      )}
      aria-label="Moderation status"
      buttonContent={
        <div className="flex gap-x-1.5 items-center">
          {mode === 'filter' ? <FilterIcon /> : <SelectedIcon />}
          {selectedName ?? 'All'}
        </div>
      }
      disabled={disabled}
    >
      {mode === 'filter' && (
        <Select.Option value={undefined} classes="text-grey-7">
          All
        </Select.Option>
      )}
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
