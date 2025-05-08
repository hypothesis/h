import { Spinner } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useState } from 'preact/hooks';

import type { Group } from '../config';
import { useGroupAnnotations } from '../hooks/use-group-annotations';
import type { APIAnnotationData } from '../utils/api';
import GroupFormHeader from './GroupFormHeader';
import type { ModerationStatus } from './ModerationStatusSelect';
import ModerationStatusSelect from './ModerationStatusSelect';
import FormContainer from './forms/FormContainer';

type AnnotationListProps = {
  filterStatus?: ModerationStatus;
  classes?: string | string[];
};

function AnnotationList({ filterStatus, classes }: AnnotationListProps) {
  const { loading, annotations } = useGroupAnnotations({ filterStatus });

  return (
    <section className={classnames('flex flex-col gap-y-2', classes)}>
      <AnnotationListContent
        loading={loading}
        annotations={annotations}
        filterStatus={filterStatus}
      />
    </section>
  );
}

type AnnotationListContentProps = AnnotationListProps & {
  loading: boolean;
  annotations: APIAnnotationData[];
};

function AnnotationListContent({
  loading,
  annotations,
  filterStatus,
}: AnnotationListContentProps) {
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
    <article key={anno.id} className="border rounded p-2">
      {anno.text}
    </article>
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
      <AnnotationList filterStatus={filterStatus} classes="mt-4" />
    </FormContainer>
  );
}
