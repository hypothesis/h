import { Spinner } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';

import type { Group } from '../config';
import { useGroupAnnotations } from '../hooks/use-group-annotations';
import GroupFormHeader from './GroupFormHeader';
import type { ModerationStatus } from './ModerationStatusSelect';
import ModerationStatusSelect from './ModerationStatusSelect';
import FormContainer from './forms/FormContainer';

function AnnotationsList({
  filterStatus,
}: {
  filterStatus?: ModerationStatus;
}) {
  const { loading, annotations } = useGroupAnnotations({ filterStatus });

  if (loading) {
    return (
      <div className="mx-auto">
        <Spinner size="md" />
      </div>
    );
  }

  if (annotations.length === 0) {
    return (
      <div
        className="border rounded p-2 text-center"
        data-testid="annotations-fallback-message"
      >
        {filterStatus === 'PENDING'
          ? 'You are all set!'
          : 'No annotations found for selected status'}
      </div>
    );
  }

  return annotations.map(anno => (
    <div key={anno.id} className="border rounded p-2">
      {anno.text}
    </div>
  ));
}

export type GroupModerationProps = {
  /** The group to be moderated */
  group: Group;
};

export default function GroupModeration({ group }: GroupModerationProps) {
  const [filterStatus, setFilterStatus] = useState<
    ModerationStatus | undefined
  >('PENDING');
  return (
    <FormContainer>
      <GroupFormHeader title="Moderate group" group={group} />
      <div className="flex justify-end">
        <ModerationStatusSelect
          selected={filterStatus}
          onChange={setFilterStatus}
        />
      </div>
      <div className="flex flex-col gap-y-2 mt-4">
        <AnnotationsList filterStatus={filterStatus} />
      </div>
    </FormContainer>
  );
}
