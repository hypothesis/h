import { useMemo, useState } from 'preact/hooks';

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

function TypeField({ defaultValue }: { defaultValue: string }) {
  return (
    <div className="form-input">
      <label className="form-input__label" htmlFor="group_type">
        Group Type
      </label>
      <select
        name="group_type"
        id="group_type"
        required
        className="form-input__input has-label"
      >
        <option value="restricted" selected={defaultValue === 'restricted'}>
          Restricted
        </option>
        <option value="open" selected={defaultValue === 'open'}>
          Open
        </option>
      </select>
    </div>
  );
}

function NameField({
  defaultValue,
  error,
}: {
  defaultValue: string;
  error: string | undefined;
}) {
  return (
    <div className={`form-input ${error ? 'is-error' : ''}`}>
      <label className="form-input__label" htmlFor="name">
        Group Name
      </label>
      <input
        type="text"
        name="name"
        id="name"
        required
        defaultValue={defaultValue}
        data-maxlength="25"
        className="form-input__input has-label"
      />
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

type Organization = {
  label: string;
  pubid: string;
};

function OrganizationField({
  organizations,
  defaultValue,
}: {
  organizations: Organization[];
  defaultValue: string;
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
    <div className="form-input">
      <label className="form-input__label" htmlFor="organization">
        Organization
      </label>
      <select
        name="organization"
        id="organization"
        className="form-input__input has-label"
      >
        <option value="">-- None --</option>
        {organizationOptions}
      </select>
    </div>
  );
}

function CreatorField({ defaultValue }: { defaultValue: string }) {
  return (
    <div className="form-input">
      <label className="form-input__label" htmlFor="creator">
        Creator
      </label>
      <input
        type="text"
        name="creator"
        id="creator"
        defaultValue={defaultValue}
        required
        className="form-input__input has-label"
      />
    </div>
  );
}

function DescriptionField({ defaultValue }: { defaultValue: string }) {
  return (
    <div className="form-input">
      <label className="form-input__label" htmlFor="description">
        Description
      </label>
      <textarea
        name="description"
        id="description"
        defaultValue={defaultValue}
        rows={3}
        data-maxlength="250"
        className="form-input__input has-label"
      />
    </div>
  );
}

function EnforceScopeField({ defaultChecked }: { defaultChecked: boolean }) {
  return (
    <div className="form-input">
      <label className="form-input__label" htmlFor="enforce_scope">
        Enfore Scope
      </label>
      <div className="form-checkbox form-checkbox--inline">
        <input
          type="checkbox"
          className="form-checkbox__input"
          name="enforce_scope"
          id="enforce_scope"
          defaultChecked={defaultChecked}
        />
      </div>
    </div>
  );
}

function ScopesFields({ initialScopes }: { initialScopes: string[] }) {
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
    <div className="form-input">
      <label className="form-input__label" htmlFor="scopes">
        Scopes
      </label>
      <div className="list-input" id="scopes">
        <ul className="list-input__list">{scopeElements}</ul>
        <button className="btn" type="button" onClick={() => addScope('')}>
          Add scope
        </button>
      </div>
    </div>
  );
}

function MembersFields({ initialMembers }: { initialMembers: string[] }) {
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
    <div className="form-input">
      <label className="form-input__label" htmlFor="members">
        Members
      </label>
      <div className="list-input" id="members">
        <ul className="list-input__list">{memberElements}</ul>
        <button className="btn" type="button" onClick={() => addMember('')}>
          Add member
        </button>
      </div>
    </div>
  );
}
