import type { ComponentChildren } from 'preact';
import { useMemo, useState, useId } from 'preact/hooks';

import type { ConfigObject } from '../config';

export type AdminGroupCreateEditFormProps = {
  config: ConfigObject;
};

export default function AdminGroupCreateEditForm({
  config,
}: AdminGroupCreateEditFormProps) {
  const stylesheetLinks = useMemo(
    () =>
      config.styles.map((stylesheetURL, index) => (
        <link
          key={`${stylesheetURL}${index}`}
          rel="stylesheet"
          href={stylesheetURL}
        />
      )),
    [config],
  );

  return (
    <>
      {stylesheetLinks}
      <form method="POST">
        <input type="hidden" name="csrf_token" value={config.CSRFToken} />
        <TypeField defaultValue={config.context.group.type || ''} />
        <NameField
          defaultValue={config.context.group.name || ''}
          error={config.context.errors?.name}
        />
        <OrganizationField
          organizations={config.context.organizations}
          defaultValue={
            config.context.group.organization ||
            config.context.defaultOrganization.pubid
          }
        />
        <CreatorField
          defaultValue={
            config.context.group.creator || config.context.user.username
          }
        />
        <DescriptionField
          defaultValue={config.context.group.description || ''}
        />
        <EnforceScopeField
          defaultChecked={config.context.group.enforceScope ?? true}
        />
        <ScopesFields initialScopes={config.context.group.scopes || []} />
        <MembersFields initialMembers={config.context.group.members || []} />

        <div className="form-actions">
          <div className="u-stretch" />
          <div className="form-actions__buttons">
            <button
              name="Save"
              type="submit"
              className="form-actions__btn btn"
              value="Save"
            >
              Save
            </button>
          </div>
        </div>
      </form>

      <form method="POST" action="">
        <button className="btn btn--danger">Delete</button>
      </form>
    </>
  );
}

function FormField({
  id,
  label,
  title,
  error,
  children,
}: {
  id: string;
  label: string;
  title?: string;
  error?: string;
  children: ComponentChildren;
}) {
  return (
    <div
      className={`form-input ${error ? 'is-error' : ''}`}
      {...(title && { title: title })}
    >
      <label className="form-input__label" htmlFor={id}>
        {label}
      </label>
      {children}
      {error ? (
        <ul className="form-input__error-list">
          <li className="form-input__error-item">{error}</li>
        </ul>
      ) : (
        ''
      )}
    </div>
  );
}

function SelectField({
  label,
  name,
  title,
  required = false,
  error,
  children,
}: {
  label: string;
  name: string;
  title?: string;
  required?: boolean;
  error?: string;
  children: ComponentChildren;
}) {
  const id = useId();

  return (
    <FormField id={id} error={error} label={label} title={title}>
      <select
        id={id}
        name={name}
        required={required}
        className="form-input__input has-label"
      >
        {children}
      </select>
    </FormField>
  );
}

function TypeField({
  defaultValue,
  error,
}: {
  defaultValue: string;
  error?: string;
}) {
  return (
    <SelectField
      label="Group Type"
      name="group_type"
      error={error}
      required={true}
    >
      <option value="restricted" selected={defaultValue === 'restricted'}>
        Restricted
      </option>
      <option value="open" selected={defaultValue === 'open'}>
        Open
      </option>
    </SelectField>
  );
}

function NameField({
  defaultValue,
  error,
}: {
  defaultValue: string;
  error?: string;
}) {
  const id = useId();

  return (
    <FormField id={id} error={error} label="Group Name">
      <input
        id={id}
        type="text"
        name="name"
        required
        defaultValue={defaultValue}
        className="form-input__input has-label"
      />
    </FormField>
  );
}

type Organization = {
  label: string;
  pubid: string;
};

function OrganizationField({
  organizations,
  defaultValue,
  error,
}: {
  organizations: Organization[];
  defaultValue: string;
  error?: string;
}) {
  const organizationOptions = organizations.map(organization => (
    <option
      value={organization.pubid}
      key={organization.pubid}
      selected={organization.pubid === defaultValue}
    >
      {organization.label}
    </option>
  ));

  return (
    <SelectField
      name="organization"
      label="Organization"
      title="Organization which this group belongs to"
      error={error}
    >
      <option value="">-- None --</option>
      {organizationOptions}
    </SelectField>
  );
}

function CreatorField({
  defaultValue,
  error,
}: {
  defaultValue: string;
  error?: string;
}) {
  const id = useId();

  return (
    <FormField
      id={id}
      error={error}
      label="Creator"
      title="Username for this group's creator"
    >
      <input
        id={id}
        type="text"
        name="creator"
        defaultValue={defaultValue}
        required
        className="form-input__input has-label"
      />
    </FormField>
  );
}

function DescriptionField({
  defaultValue,
  error,
}: {
  defaultValue: string;
  error?: string;
}) {
  const id = useId();

  return (
    <FormField
      id={id}
      error={error}
      label="Description"
      title="Optional group description"
    >
      <textarea
        id={id}
        name="description"
        defaultValue={defaultValue}
        rows={3}
        className="form-input__input has-label"
      />
    </FormField>
  );
}

function EnforceScopeField({
  defaultChecked,
  error,
}: {
  defaultChecked: boolean;
  error?: string;
}) {
  const id = useId();

  return (
    <FormField id={id} error={error} label="Enforce Scope">
      <div className="form-checkbox form-checkbox--inline">
        <input
          id={id}
          type="checkbox"
          className="form-checkbox__input"
          name="enforce_scope"
          defaultChecked={defaultChecked}
        />
      </div>
    </FormField>
  );
}

function ScopesFields({ initialScopes }: { initialScopes: string[] }) {
  const id = useId();
  const [scopes, setScopes] = useState<string[]>(initialScopes);

  /**
   * Append the given `scope` to `scopes`.
   */
  const addScope = (scope: string) => {
    setScopes([...scopes, scope]);
  };

  /**
   * Replace the the scope with the given `index` with `newScope`.
   */
  const replaceScope = (index: number, newScope: string) => {
    setScopes([
      ...scopes.slice(0, index),
      newScope,
      ...scopes.slice(index + 1),
    ]);
  };

  /**
   * Remove the scope with the given `index` from `scopes`.
   */
  const removeScope = (index: number) => {
    setScopes([...scopes.slice(0, index), ...scopes.slice(index + 1)]);
  };

  const scopeElements = scopes.map((scope, index) => (
    <li className="list-input__item" key={index}>
      <div className="list-input__item-inner">
        <input
          type="text"
          name="scopes"
          className="form-input__input"
          value={scope}
          required
          onInput={e => replaceScope(index, e.currentTarget.value)}
        />
        <button
          className="list-input__remove-btn"
          title="Remove scope"
          type="button"
          onClick={() => removeScope(index)}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="10"
            height="10"
            className="svg-icon"
          >
            <path
              d="M3.586 5 1.293 7.293.586 8 2 9.414l.707-.707L5 6.414l2.293 2.293.707.707L9.414 8l-.707-.707L6.414 5l2.293-2.293L9.414 2 8 .586l-.707.707L5 3.586 2.707 1.293 2 .586.586 2l.707.707z"
              fill="currentColor"
              fillRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </li>
  ));

  return (
    <FormField id={id} label="Scopes">
      <div className="list-input" id={id}>
        <ul className="list-input__list">{scopeElements}</ul>
        <button className="btn" type="button" onClick={() => addScope('')}>
          Add scope
        </button>
      </div>
    </FormField>
  );
}

function MembersFields({ initialMembers }: { initialMembers: string[] }) {
  const id = useId();
  const [members, setMembers] = useState<string[]>(initialMembers);

  /**
   * Append the given `member` to `members`.
   */
  const addMember = (member: string) => {
    setMembers([...members, member]);
  };

  /**
   * Replace the the member with the given `index` with `newMember`.
   */
  const replaceMember = (index: number, newMember: string) => {
    setMembers([
      ...members.slice(0, index),
      newMember,
      ...members.slice(index + 1),
    ]);
  };

  /**
   * Remove the member with the given `index` from `members`.
   */
  const removeMember = (index: number) => {
    setMembers([...members.slice(0, index), ...members.slice(index + 1)]);
  };
  const memberElements = members.map((member, index) => (
    <li className="list-input__item" key={index}>
      <div className="list-input__item-inner">
        <input
          type="text"
          name="members"
          value={member}
          className="form-input__input"
          onInput={e => replaceMember(index, e.currentTarget.value)}
          required
        />
        <button
          className="list-input__remove-btn"
          title="Remove member"
          type="button"
          onClick={() => removeMember(index)}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="10"
            height="10"
            className="svg-icon"
          >
            <path
              d="M3.586 5 1.293 7.293.586 8 2 9.414l.707-.707L5 6.414l2.293 2.293.707.707L9.414 8l-.707-.707L6.414 5l2.293-2.293L9.414 2 8 .586l-.707.707L5 3.586 2.707 1.293 2 .586.586 2l.707.707z"
              fill="currentColor"
              fillRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </li>
  ));

  return (
    <FormField id={id} label="Members">
      <div className="list-input" id={id}>
        <ul className="list-input__list">{memberElements}</ul>
        <button className="btn" type="button" onClick={() => addMember('')}>
          Add member
        </button>
      </div>
    </FormField>
  );
}
