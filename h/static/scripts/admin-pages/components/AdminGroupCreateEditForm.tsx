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

  const [scopes, setScopes] = useState<string[]>([]);

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
          name="scope"
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

  type Membership = {
    username: string;
  };

  const [memberships, setMemberships] = useState<Membership[]>([]);

  /**
   * Append the given `membership` to `memberships`.
   */
  const addMembership = (membership: Membership) => {
    setMemberships([...memberships, membership]);
  };

  /**
   * Replace the the membership with the given `index` with `newMembership`.
   */
  const replaceMembership = (index: number, newMembership: Membership) => {
    setMemberships([
      ...memberships.slice(0, index),
      newMembership,
      ...memberships.slice(index + 1),
    ]);
  };

  /**
   * Remove the membership with the given `index` from `memberships`.
   */
  const removeMembership = (index: number) => {
    setMemberships([
      ...memberships.slice(0, index),
      ...memberships.slice(index + 1),
    ]);
  };

  const membershipElements = memberships.map((membership, index) => (
    <li className="list-input__item" key={index}>
      <div className="list-input__item-inner">
        <input
          type="text"
          name="membership"
          value={membership.username}
          className="form-input__input"
          onInput={e =>
            replaceMembership(index, { username: e.currentTarget.value })
          }
          required
        />
        <button
          className="list-input__remove-btn"
          title="Remove member"
          type="button"
          onClick={() => removeMembership(index)}
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

  const organizationOptions = config.context.organizations.map(organization => (
    <option value={organization.pubid} key={organization.pubid}>
      {organization.label}
    </option>
  ));

  return (
    <>
      {stylesheetLinks}
      <form method="POST">
        <input type="hidden" name="csrf_token" value={config.CSRFToken} />

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
            <option selected>Select</option>
            <option value="restricted">Restricted</option>
            <option value="open">Open</option>
          </select>
        </div>

        <div className="form-input">
          <label className="form-input__label" htmlFor="name">
            Group Name
          </label>
          <input
            type="text"
            name="name"
            id="name"
            required
            value=""
            data-maxlength="25"
            className="form-input__input has-label"
          />
        </div>

        <div className="form-input">
          <label className="form-input__label" htmlFor="organization">
            Organization
          </label>
          <select
            name="organization"
            id="organization"
            value={config.context.defaultOrganization.pubid}
            className="form-input__input has-label"
          >
            <option value="">-- None --</option>
            {organizationOptions}
          </select>
        </div>

        <div className="form-input">
          <label className="form-input__label" htmlFor="creator">
            Creator
          </label>
          <input
            type="text"
            name="creator"
            id="creator"
            value={config.context.user.username}
            required
            className="form-input__input has-label"
          />
        </div>

        <div className="form-input">
          <label className="form-input__label" htmlFor="description">
            Description
          </label>
          <textarea
            name="description"
            id="description"
            value=""
            rows={3}
            data-maxlength="250"
            className="form-input__input has-label"
          />
        </div>

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
              checked
            />
          </div>
        </div>

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

        <div className="form-input">
          <label className="form-input__label" htmlFor="members">
            Members
          </label>
          <div className="list-input" id="members">
            <ul className="list-input__list">{membershipElements}</ul>
            <button
              className="btn"
              type="button"
              onClick={() => addMembership({ username: '' })}
            >
              Add member
            </button>
          </div>
        </div>

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
