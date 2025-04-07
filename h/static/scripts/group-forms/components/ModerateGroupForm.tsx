import {
  DataTable,
  Scroll,
  Pagination,
  Select,
} from '@hypothesis/frontend-shared';
import { useCallback, useContext, useEffect, useState } from 'preact/hooks';

import { Config } from '../config';
import type { APIConfig, Group } from '../config';
import type { Annotation, AnnotationModerationStatus, GroupAnnotationsResponse } from '../utils/api';
import { callAPI } from '../utils/api';
import type { APIError } from '../utils/api';
import FormContainer from './forms/FormContainer';
import ErrorNotice from './ErrorNotice';
import GroupFormHeader from './GroupFormHeader';

type TableColumn<Row> = {
  field: keyof Row;
  label: string;
  classes?: string;
};

type AnnotationRow = {
  id: string,
  text: string,
  moderation_status: AnnotationModerationStatus,
  created: string,

  /** True if an operation is currently being performed against this annotation. */
  busy: boolean;

};

/**
 * Mappings between roles and labels. The keys are sorted in descending order
 * of permissions.
 */
const statusesStrings: Record<AnnotationModerationStatus, string> = {
  denied: 'Denied',
  APPROVED: 'Approved',
  pending: 'Pending',
  private: 'Private', // TODO IS this relevant here, I don't think  private ones should appear 
  spam: 'Spam',
};
const possibleStatuses: AnnotationModerationStatus[] = Object.keys(statusesStrings) as AnnotationModerationStatus[];

function annotationToRow(annotation: Annotation): AnnotationRow {
  return {
    id: annotation.id,
    text: annotation.text,
    created: annotation.created,
    moderation_status: annotation.moderation_status,
    busy: false
  };
}

async function fetchAnnotations(
  api: APIConfig,
  options: {
    signal: AbortSignal;
    pageNumber: number;
    pageSize: number;
  },
): Promise<{ total: number; annotations: AnnotationRow[] }> {
  const { pageNumber, pageSize, signal } = options;
  const { url, method, headers } = api;
  const { meta, data }: GroupAnnotationsResponse = await callAPI(url, {
    headers,
    pageSize,
    method,
    pageNumber,
    signal,
  });

  return {
    total: meta.page.total,
    annotations: data.map(a => annotationToRow(a)),
  };
}


async function setModerationStatus(
  api: APIConfig,
  annotation_id: string,
  moderation_status: AnnotationModerationStatus,
): Promise<Annotation> {
  const { url: urlTemplate, method, headers } = api;
  const url = urlTemplate.replace(':annotation_id', encodeURIComponent(annotation_id));
  return callAPI(url, {
    method,
    headers,
    json: {
      moderation_status,
    },
  });
}

type StatusSelectProps = {
  annotation_id: string;

  disabled?: boolean;

  /** The current role of the member. */
  current: AnnotationModerationStatus;

  /** Callback for when the user requests to change the role of the member. */
  onChange: (r: AnnotationModerationStatus) => void;
};

function StatusSelect({
  annotation_id,
  disabled = false,
  current,
  onChange,
}: StatusSelectProps) {
  return (
    <Select
      value={current}
      onChange={onChange}
      buttonContent={[current]}
      data-testid={`status-${annotation_id}`}
      disabled={disabled}
    >
      {possibleStatuses.map(status => (
        <Select.Option key={status} value={status}>
          {statusesStrings[status]}
        </Select.Option>
      ))}
    </Select>
  );
}

const defaultDateFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: '2-digit',
});

export const pageSize = 20;

export type ModerateGroupMembersFormProps = {
  /** The saved group details. */
  group: Group;

  dateFormatter?: Intl.DateTimeFormat;
};

export default function ModerateGroupForm({
  group,
  dateFormatter = defaultDateFormatter,
}: ModerateGroupMembersFormProps) {
  const config = useContext(Config)!;

  const [pageNumber, setPageNumber] = useState(1);
  const [totalAnnotations, setTotalAnnotations] = useState<number | null>(null);
  const totalPages =
    totalAnnotations !== null ? Math.ceil(totalAnnotations / pageSize) : null;
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const setError = useCallback((context: string, err: Error) => {
    const apiErr = err as APIError;
    if (apiErr.aborted) {
      return;
    }
    const message = `${context}: ${err.message}`;
    setErrorMessage(message);
  }, []);

  // Fetch group members when the form loads.
  const [annotations, setAnnotations] = useState<AnnotationRow[] | null>(null);
  useEffect(() => {
    // istanbul ignore next
    if (!config.api.readGroupAnnotations) {
      throw new Error('readGroupAnnotations API config missing');
    }
    const abort = new AbortController();
    setErrorMessage(null);
    fetchAnnotations(config.api.readGroupAnnotations, {
      pageNumber,
      pageSize,
      signal: abort.signal,
    })
      .then(({ total, annotations }) => {
        setAnnotations(annotations);
        setTotalAnnotations(total);
      })
      .catch(err => {
        setError('Failed to fetch group members', err);
      });
    return () => {
      abort.abort();
    };
  }, [config.api.readGroupAnnotations, pageNumber, setError]);

  const columns: TableColumn<AnnotationRow>[] = [
    {
      field: 'id',
      label: 'id',
    },
    {
      field: 'text',
      label: 'text',
    },
    {
      field: 'moderation_status',
      label: 'status',
    },

  ];

  const updateAnnotation = (annotation_id: string, update: Partial<AnnotationRow>) => {
    setAnnotations(
      annotations =>
        annotations?.map(a => {
          return a.id === annotation_id ? { ...a, ...update } : a;
        }) ?? null,
    );
  };



  const changeStatus = useCallback(
    async (annotation: AnnotationRow, moderation_status: AnnotationModerationStatus) => {
      updateAnnotation(annotation.id, { moderation_status, busy: true });
      try {
        const updatedAnnotation = await setModerationStatus(
          config.api.changeAnnotationModerationStatus!,
          annotation.id,
          moderation_status,
        );
        updateAnnotation(annotation.id, annotationToRow(updatedAnnotation));
      } catch (err) {
        setError('Failed to change', err);
      }
    },
    [config.api.changeAnnotationModerationStatus, setError],
  );

  const renderRow = useCallback(
    (annotation: AnnotationRow, field: keyof AnnotationRow) => {
      switch (field) {
        case 'id':
          return (
            <span data-testid="id" className="font-bold text-grey-7">
              {annotation.id}
            </span>

          )
        case 'text':
          return (
            <span data-testid="id" className="font-bold text-grey-7">
              {annotation.text}
            </span>

          )

        case 'created':
          return (
            <span data-testid={`created-${annotation.id}`}>
              {dateFormatter.format(annotation.created)}
            </span>
          );

        case 'moderation_status':
          return (
            <StatusSelect
              annotation_id={annotation.id}
              current={annotation.moderation_status}
              onChange={status => changeStatus(annotation, status)}
              disabled={annotation.busy}
            />
          );


        // istanbul ignore next
        default:
          return null;
      }
    },
    [changeStatus, dateFormatter],
  );

  return (
    <>
      <FormContainer>
        <GroupFormHeader title="Moderate group" group={group} />
        <ErrorNotice message={errorMessage} />
        <div className="w-full">
          <Scroll>
            <DataTable
              grid
              striped={false}
              title="Group annotations"
              rows={annotations ?? []}
              columns={columns}
              renderItem={renderRow}
              loading={!annotations}
            />
          </Scroll>
        </div>
        {typeof totalPages === 'number' && totalPages > 1 && (
          <div className="mt-4 flex justify-center">
            <Pagination
              currentPage={pageNumber}
              onChangePage={setPageNumber}
              totalPages={totalPages}
            />
          </div>
        )}
      </FormContainer>
    </>
  );
}
