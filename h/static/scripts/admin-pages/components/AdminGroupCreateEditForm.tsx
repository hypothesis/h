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

  const [memberships, setMemberships] = useState([]);

  const membershipElements = memberships.map((membership, index) => (
    <li className="list-input__item" key={index}>
      <div className="list-input__item-inner">
        <input
          type="text"
          name="membership"
          value={membership.username}
          className="form-input__input"
          required
        />
        <button
          className="list-input__remove-btn"
          title="Remove item"
          type="button"
          onClick={() =>
            setMemberships([
              ...memberships.slice(0, index),
              ...memberships.slice(index + 1),
            ])
          }
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
            <ul className="list-input__list" />
            <button className="btn" type="button">
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
              onClick={() => setMemberships([...memberships, { username: '' }])}
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
