export default function AdminGroupCreateEditForm() {
  return (
    <>
      <form method="POST">
        <div class="form-input">
          <label class="form-input__label" for="group_type">Group Type</label>
          <select name="group_type" id="group_type" value="restricted" required class="form-input__input has-label">
            <option selected>Select</option>
            <option value="restricted">Restricted</option>
            <option value="open">Open</option>
          </select>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="name">Group Name</label>
          <input type="text" name="name" id="name" required value="" data-maxlength="25" class="form-input__input has-label"></input>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="organization">Organization</label>
          <select name="organization" id="organization" value="" class="form-input__input has-label">
            <option value="">-- None --</option>
          </select>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="creator">Creator</label>
          <input type="text" name="creator" id="creator" value="" required class="form-input__input has-label"></input>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="description">Description</label>
          <textarea rows="3" name="description" id="description" value="" rows="3" data-maxlength="250" class="form-input__input has-label"></textarea>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="enforce_scope">Enfore Scope</label>
          <div class="form-checkbox form-checkbox--inline">
            <input type="checkbox" class="form-checkbox__input" name="enforce_scope" id="enforce_scope" checked></input>
          </div>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="scopes">Scopes</label>
          <div class="list-input" id="scopes">
            <ul class="list-input__list">
            </ul>
            <button class="btn" type="button">Add scope</button>
          </div>
        </div>

        <div class="form-input">
          <label class="form-input__label" for="members">Members</label>
          <div class="list-input" id="members">
            <ul class="list-input__list">
            </ul>
            <button class="btn" type="button">Add member</button>
          </div>
        </div>

        <div class="form-actions">
          <div class="u-stretch"></div>
          <div class="form-actions__buttons">
            <button name="Save" type="submit" class="form-actions__btn btn" value="Save">Save</button>
          </div>
        </div>
      </form>

      <form method="POST" action="">
        <button class="btn btn--danger">Delete</button>
      </form>
    </>
  );
}
