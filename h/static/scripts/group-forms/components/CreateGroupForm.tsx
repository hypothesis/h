export default function CreateGroupForm() {
  return (
    <>
      <h1 class="form-header">Create a new private group</h1>

      <form class="form group-form__form">
        <div class="form-input">
          <label for="name" class="form-input__label group-form__name-label">
            Name <span class="form-input__required">*</span>
          </label>
          <input
            type="text"
            id="name"
            class="form-input__input group-form__name-input has-label"
            autofocus=""
            autocomplete="off"
            required
          />
          <span class="form-input__character-counter is-ready">0/25</span>
        </div>

        <div class="form-input">
          <label
            class="form-input__label group-form__description-label"
            for="description"
          >
            Description
          </label>
          <textarea
            id="description"
            class="form-input__input group-form__description-input has-label"
          ></textarea>
          <span class="form-input__character-counter is-ready">0/250</span>
        </div>

        <div class="form-actions">
          <div class="u-stretch"></div>

          <div class="form-actions__buttons">
            <button class="form-actions__btn btn primary-action-btn group-form__submit-btn">
              Create group
            </button>
          </div>
        </div>
      </form>

      <footer class="form-footer">
        <span class="form-footer__required">
          <span class="form-footer__symbol">*</span>
          <span class="form-footer__text">Required</span>
        </span>
      </footer>
    </>
  );
}
