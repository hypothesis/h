import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { LoginFormsConfig } from '../../config';
import NotificationsForm from '../NotificationsForm';

describe('NotificationsForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      features: {},
      hasEmail: true,
      form: {
        data: {
          reply: true,
          mention: true,
          moderation: true,
        },
        errors: {},
      },
    };
  });

  const getElements = wrapper => {
    return {
      form: wrapper.find('form[data-testid="form"]'),
      csrfInput: wrapper.find('input[name="csrf_token"]'),
      replyCheckbox: wrapper.find('Checkbox[data-testid="reply-checkbox"]'),
      mentionCheckbox: wrapper.find('Checkbox[data-testid="mention-checkbox"]'),
      moderationCheckbox: wrapper.find(
        'Checkbox[data-testid="moderation-checkbox"]',
      ),
      submitButton: wrapper.find('Button[data-testid="submit-button"]'),
      callout: wrapper.find('Callout'),
    };
  };

  const createWrapper = () => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <NotificationsForm />
      </LoginFormsConfig.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  describe('when user has email', () => {
    it('renders the notification settings form', () => {
      const { elements } = createWrapper();
      const { form, replyCheckbox, mentionCheckbox, moderationCheckbox } =
        elements;

      assert.isTrue(form.exists());
      assert.isTrue(replyCheckbox.exists());
      assert.isTrue(mentionCheckbox.exists());
      assert.isTrue(moderationCheckbox.exists());
      assert.isFalse(elements.callout.exists());
    });

    it('pre-fills checkboxes from form data', () => {
      fakeConfig.form.data = {
        reply: false,
        mention: true,
        moderation: false,
      };

      const { elements } = createWrapper();
      const { replyCheckbox, mentionCheckbox, moderationCheckbox } = elements;

      assert.equal(replyCheckbox.prop('checked'), false);
      assert.equal(mentionCheckbox.prop('checked'), true);
      assert.equal(moderationCheckbox.prop('checked'), false);
    });

    it('sets correct checkbox names and values', () => {
      const { elements } = createWrapper();
      const { replyCheckbox, mentionCheckbox, moderationCheckbox } = elements;

      assert.equal(replyCheckbox.prop('name'), 'reply');
      assert.equal(replyCheckbox.prop('value'), 'true');
      assert.equal(mentionCheckbox.prop('name'), 'mention');
      assert.equal(mentionCheckbox.prop('value'), 'true');
      assert.equal(moderationCheckbox.prop('name'), 'moderation');
      assert.equal(moderationCheckbox.prop('value'), 'true');
    });

    [
      { field: 'replyCheckbox', name: 'reply' },
      { field: 'mentionCheckbox', name: 'mention' },
      { field: 'moderationCheckbox', name: 'moderation' },
    ].forEach(({ field, name }) => {
      it(`updates ${name} checkbox when clicked`, () => {
        const { wrapper, elements } = createWrapper();

        act(() => {
          const event = {
            target: { checked: false },
          };
          elements[field].prop('onChange')(event);
        });
        wrapper.update();
        const updatedElements = getElements(wrapper);

        assert.equal(updatedElements[field].prop('checked'), false);
      });
    });
  });

  describe('when user has no email', () => {
    beforeEach(() => {
      fakeConfig.hasEmail = false;
    });

    it('displays callout message instead of form', () => {
      const { elements } = createWrapper();
      const { form, callout } = elements;

      assert.isFalse(form.exists());
      assert.isTrue(callout.exists());
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
