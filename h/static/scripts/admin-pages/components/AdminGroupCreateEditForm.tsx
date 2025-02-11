import { useMemo } from 'preact/hooks';

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

        <div className="form-input">
          <label className="form-input__label" htmlFor="group_type">
            Group Type
          </label>
          <select
            name="group_type"
            id="group_type"
            value="restricted"
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
            value=""
            className="form-input__input has-label"
          >
            <option value="">-- None --</option>
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
            value=""
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
            <ul className="list-input__list" />
            <button className="btn" type="button">
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
