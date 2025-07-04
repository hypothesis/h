import {
  checkAccessibility,
  delay,
  mount,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import {
  $imports,
  default as CreateEditGroupForm,
} from '../CreateEditGroupForm';

describe('CreateEditGroupForm', () => {
  let config;
  let fakeCallAPI;
  let fakeSetLocation;
  let fakeUseUnsavedChanges;

  function navigateWarningActive() {
    return fakeUseUnsavedChanges.lastCall.args[0] === true;
  }

  beforeEach(() => {
    config = {
      api: {
        createGroup: {
          method: 'POST',
          url: 'https://example.com/api/groups',
        },
      },
      context: {
        group: null,
      },
      features: {
        group_type: true,
      },
    };

    fakeCallAPI = sinon.stub();
    fakeSetLocation = sinon.stub();
    fakeUseUnsavedChanges = sinon.stub();

    $imports.$mock({
      '../utils/api': {
        callAPI: fakeCallAPI,
      },
      '../../forms-common/unsaved-changes': {
        useUnsavedChanges: fakeUseUnsavedChanges,
      },
      '../utils/set-location': {
        setLocation: fakeSetLocation,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const getSelectedGroupType = wrapper => {
    return wrapper.find('[data-testid="group-type"]').prop('selected');
  };

  const setSelectedGroupType = (wrapper, newType) => {
    const radioGroup = wrapper.find('[data-testid="group-type"]');
    act(() => {
      radioGroup.prop('onChange')(newType);
    });
    wrapper.update();
  };

  /** Save the form and wait until the request completes. */
  async function saveChanges(wrapper) {
    wrapper.find('form[data-testid="form"]').simulate('submit');
    await waitForElement(
      wrapper,
      `button[data-testid="button"][disabled=false]`,
    );
  }

  const getElements = wrapper => {
    return {
      header: wrapper.find('GroupFormHeader'),
      nameField: wrapper.find('TextField[label="Name"]'),
      descriptionField: wrapper.find('TextField[label="Description"]'),
      submitButton: wrapper.find('button[data-testid="button"]'),
    };
  };

  const preModerationCheckbox = wrapper =>
    wrapper.find('Checkbox[data-testid="pre-moderation"]');

  const isPreModerationEnabled = wrapper =>
    preModerationCheckbox(wrapper).prop('checked');

  const changePreModerationCheckbox = (wrapper, checked) => {
    act(() =>
      preModerationCheckbox(wrapper).props().onChange({
        target: { checked },
      }),
    );
    wrapper.update();
  };

  const createWrapper = (props = {}) => {
    const wrapper = mount(
      <Config.Provider value={config}>
        <CreateEditGroupForm group={config.context.group} {...props} />
      </Config.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  [
    {
      groupTypeFlag: true,
      heading: 'Create a new group',
    },
    {
      groupTypeFlag: false,
      heading: 'Create a new private group',
    },
  ].forEach(({ groupTypeFlag, heading }) => {
    it('displays a create-new-group form', async () => {
      config.features.group_type = groupTypeFlag;

      const { wrapper, elements } = createWrapper();
      const { header, nameField, descriptionField, submitButton } = elements;

      assert.equal(header.prop('title'), heading);
      assert.equal(nameField.prop('value'), '');
      assert.equal(descriptionField.prop('value'), '');
      assert.equal(submitButton.text(), 'Create group');
      assert.isFalse(wrapper.exists('[data-testid="back-link"]'));
      assert.isFalse(wrapper.exists('[data-testid="error-message"]'));

      if (groupTypeFlag) {
        assert.equal(getSelectedGroupType(wrapper), 'private');
      }

      await assertInLoadingState(wrapper, false);
      assert.isFalse(savedConfirmationShowing(wrapper));
    });
  });

  it('does not warn when leaving page if there are unsaved changes', () => {
    const { elements } = createWrapper();

    act(() => {
      elements.nameField.prop('onChangeValue')('modified');
    });

    // Warnings about unsaved changes are only enabled when editing a group.
    // See notes in the implementation.
    assert.isFalse(navigateWarningActive());
  });

  it('shows a loading state when the create-group API request is in-flight', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves(new Promise(() => {}));

    wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  it('continues to show the loading state after receiving a successful API response', async () => {
    const { wrapper } = createWrapper();
    fakeCallAPI.resolves({ links: { html: 'https://example.com/group/foo' } });

    wrapper.find('form[data-testid="form"]').simulate('submit');

    await assertInLoadingState(wrapper, true);
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  [
    {
      name: 'Test group name',
      description: 'Test description',
      type: 'private',
    },
    {
      name: 'Test group name',
      description: 'Test description',
      type: 'restricted',
    },
    {
      name: 'Test group name',
      description: 'Test description',
      type: 'open',
    },
  ].forEach(({ name, description, type }) => {
    it('creates the group and redirects the browser', async () => {
      const { wrapper, elements } = createWrapper();
      const { nameField, descriptionField } = elements;
      const groupURL = 'https://example.com/group/foo';
      fakeCallAPI.resolves({ links: { html: groupURL } });

      nameField.prop('onChangeValue')(name);
      descriptionField.prop('onChangeValue')(description);
      setSelectedGroupType(wrapper, type);

      wrapper.find('form[data-testid="form"]').simulate('submit');
      await delay(0);

      assert.calledOnceWithExactly(fakeCallAPI, config.api.createGroup.url, {
        method: config.api.createGroup.method,
        headers: config.api.createGroup.headers,
        json: {
          name,
          description,
          type,
          pre_moderated: false,
        },
      });
      assert.calledOnceWithExactly(fakeSetLocation, groupURL);
    });
  });

  it('shows an error message if callAPI() throws an error', async () => {
    const errorMessageFromCallAPI = 'Bad API call.';
    fakeCallAPI.rejects({ message: errorMessageFromCallAPI });
    const { wrapper } = createWrapper();

    wrapper.find('form[data-testid="form"]').simulate('submit');

    const errorMessageEl = await waitForElement(
      wrapper,
      '[data-testid="error-message"]',
    );
    assert.equal(errorMessageEl.text(), errorMessageFromCallAPI);
    // It exits its loading state after receiving an error response.
    await assertInLoadingState(wrapper, false);
    assert.isFalse(savedConfirmationShowing(wrapper));
  });

  describe('pre-moderation', () => {
    [true, false].forEach(preModerationEnabled => {
      it('shows pre-moderation checkbox when group moderation is enabled', () => {
        config.features.pre_moderation = preModerationEnabled;
        const { wrapper } = createWrapper();

        assert.equal(
          preModerationCheckbox(wrapper).exists(),
          preModerationEnabled,
        );
      });
    });

    it('toggles pre-moderation by clicking on it', () => {
      config.features.pre_moderation = true;
      const { wrapper } = createWrapper();

      assert.isFalse(isPreModerationEnabled(wrapper));
      changePreModerationCheckbox(wrapper, true);
      assert.isTrue(isPreModerationEnabled(wrapper));
    });
  });

  context('when editing an existing group', () => {
    beforeEach(() => {
      config.context.group = {
        pubid: 'testid',
        name: 'Test Name',
        description: 'Test group description',
        link: 'https://example.com/groups/testid',

        // Set this to a non-default value.
        type: 'open',
      };
      config.api.updateGroup = {
        method: 'PATCH',
        url: 'https://example.com/api/group/foo',
      };
    });

    it('displays an edit-group form', async () => {
      const group = {
        name: 'Original name',
        description: 'Original description',
        type: 'restricted', // Non-default value
      };
      const { wrapper, elements } = createWrapper({ group });
      const { header, nameField, descriptionField, submitButton } = elements;

      assert.equal(header.prop('title'), 'Edit group');
      assert.equal(nameField.prop('value'), group.name);
      assert.equal(descriptionField.prop('value'), group.description);
      assert.equal(getSelectedGroupType(wrapper), group.type);
      assert.equal(submitButton.text(), 'Save changes');
      assert.isFalse(wrapper.exists('[data-testid="error-message"]'));
      await assertInLoadingState(wrapper, false);
      assert.isFalse(savedConfirmationShowing(wrapper));
    });

    it('warns when closing tab if there are unsaved changes', async () => {
      const { wrapper, elements } = createWrapper();
      const { nameField, descriptionField } = elements;
      assert.isFalse(navigateWarningActive());

      act(() => {
        nameField.prop('onChangeValue')('foo');
      });
      assert.isTrue(navigateWarningActive());

      wrapper.find('form[data-testid="form"]').simulate('submit');
      // Warning should still be active in saving state.
      assert.isTrue(navigateWarningActive());
      await waitForElement(wrapper, 'SaveStateIcon[state="saved"]');

      // Warning should be disabled once saved.
      assert.isFalse(navigateWarningActive());

      // Warning should be re-enabled if we then edit the form again.
      act(() => {
        descriptionField.prop('onChangeValue')('bar');
      });
      assert.isTrue(navigateWarningActive());

      // Warning should remain active if form is edited while being saved.
      wrapper.find('form[data-testid="form"]').simulate('submit');
      act(() => {
        nameField.prop('onChangeValue')('bar');
      });
      await delay(0);
      assert.isTrue(navigateWarningActive());
    });

    it('clears modified state when page is loaded from cache', () => {
      const { elements } = createWrapper();
      act(() => {
        elements.nameField.prop('onChangeValue')('modified');
      });
      assert.isTrue(navigateWarningActive());

      act(() => {
        window.dispatchEvent(
          new PageTransitionEvent('pageshow', { persisted: true }),
        );
      });
      assert.isFalse(navigateWarningActive());
    });

    it('updates the group', async () => {
      config.features.pre_moderation = true;
      const onUpdateGroup = sinon.stub();
      const { wrapper, elements } = createWrapper({ onUpdateGroup });
      const { nameField, descriptionField } = elements;

      // Modify all group properties.
      const name = 'Edited Group Name';
      const description = 'Edited group description';
      const newGroupType = 'restricted';

      act(() => {
        nameField.prop('onChangeValue')(name);
        descriptionField.prop('onChangeValue')(description);
      });
      wrapper.find(`[data-value="${newGroupType}"]`).simulate('click');
      changePreModerationCheckbox(wrapper, true);

      wrapper.find('form[data-testid="form"]').simulate('submit');

      // Check all updated properties were sent in API request.
      assert.isTrue(
        fakeCallAPI.calledOnceWithExactly(config.api.updateGroup.url, {
          method: config.api.updateGroup.method,
          headers: config.api.updateGroup.headers,
          json: {
            id: config.context.group.pubid,
            name,
            description,
            type: newGroupType,
            pre_moderated: true,
          },
        }),
      );

      // Check all updated properties were persisted via `onUpdateGroup` callback.
      await assertInLoadingState(wrapper, false);
      assert.calledWith(
        onUpdateGroup,
        sinon.match({
          ...config.context.group,
          name,
          description,
          type: newGroupType,
          pre_moderated: true,
        }),
      );
    });

    it('shows a loading state when the update-group API request is in-flight', async () => {
      const { wrapper } = createWrapper();
      fakeCallAPI.resolves(new Promise(() => {}));

      wrapper.find('form[data-testid="form"]').simulate('submit');

      await assertInLoadingState(wrapper, true);
    });

    it('shows a confirmation after receiving a successful API response', async () => {
      const { wrapper } = createWrapper();
      fakeCallAPI.resolves();

      wrapper.find('form[data-testid="form"]').simulate('submit');

      await assertInLoadingState(wrapper, false);
      assert.isTrue(savedConfirmationShowing(wrapper));
    });

    it('shows an error message if callAPI() throws an error', async () => {
      const errorMessageFromCallAPI = 'Bad API call.';
      fakeCallAPI.rejects(new Error(errorMessageFromCallAPI));
      const { wrapper } = createWrapper();

      wrapper.find('form[data-testid="form"]').simulate('submit');

      const errorMessageEl = await waitForElement(
        wrapper,
        '[data-testid="error-message"]',
      );
      assert.equal(errorMessageEl.text(), errorMessageFromCallAPI);
      await assertInLoadingState(wrapper, false);
      assert.isFalse(savedConfirmationShowing(wrapper));
    });

    ['name', 'description', 'type'].forEach(field => {
      it('clears the confirmation if fields are edited again', async () => {
        const { wrapper, elements } = createWrapper();
        fakeCallAPI.resolves();
        wrapper.find('form[data-testid="form"]').simulate('submit');

        if (field === 'type') {
          // nb. Since the group has no annotations, the type will change
          // immediately.
          setSelectedGroupType(wrapper, 'open');
        } else if (field === 'name') {
          elements.nameField.prop('onChangeValue')('new text');
        } else if (field === 'description') {
          elements.descriptionField.prop('onChangeValue')('new text');
        }

        await assertInLoadingState(wrapper, false);
        assert.isFalse(savedConfirmationShowing(wrapper));
      });
    });

    it('clears confirmation when type is changed with a warning', async () => {
      // Trigger warning when changing group type
      config.context.group = {
        ...config.context.group,
        num_annotations: 2,
        type: 'private',
      };
      const { wrapper } = createWrapper();

      fakeCallAPI.resolves();
      await saveChanges(wrapper);
      assert.isTrue(savedConfirmationShowing(wrapper));

      // Change group type. The save state is not cleared immediately as a
      // warning is shown.
      setSelectedGroupType(wrapper, 'open');
      assert.isTrue(savedConfirmationShowing(wrapper));

      // When the change is confirmed, the form is marked as unsaved.
      const warning = wrapper.find('WarningDialog');
      act(() => warning.prop('onConfirm')());
      wrapper.update();
      assert.isFalse(savedConfirmationShowing(wrapper));
    });

    it('marks form as unsaved if pre-moderation checkbox changes', () => {
      config.features.pre_moderation = true;
      const { wrapper } = createWrapper();

      assert.isFalse(navigateWarningActive());
      changePreModerationCheckbox(wrapper, true);
      assert.isTrue(navigateWarningActive());
    });
  });

  [
    // Do not warn when changing from the default type of "private" to a public
    // type, when creating a new group.
    {
      oldType: null,
      newType: 'open',
      expectedWarning: null,
      annotationCount: 0,
    },
    {
      // Warn when making annotations public (open group)
      oldType: 'private',
      newType: 'open',
      annotationCount: 2,
      expectedWarning: {
        title: 'Make 2 annotations public?',
        message:
          'Are you sure you want to make "Test Name" an open group? 2 annotations that are visible only to members of "Test Name" will become publicly visible.',
        confirmAction: 'Make annotations public',
      },
    },
    {
      // Warn when making annotations public (singular)
      oldType: 'private',
      newType: 'open',
      annotationCount: 1,
      expectedWarning: {
        title: 'Make 1 annotation public?',
        message:
          'Are you sure you want to make "Test Name" an open group? 1 annotation that is visible only to members of "Test Name" will become publicly visible.',
        confirmAction: 'Make annotations public',
      },
    },
    {
      // Warn when making annotations public (restricted group)
      oldType: 'private',
      newType: 'restricted',
      annotationCount: 5,
      expectedWarning: {
        title: 'Make 5 annotations public?',
        message:
          'Are you sure you want to make "Test Name" a restricted group? 5 annotations that are visible only to members of "Test Name" will become publicly visible.',
        confirmAction: 'Make annotations public',
      },
    },
    {
      // Warn when making annotations private
      oldType: 'open',
      newType: 'private',
      annotationCount: 3,
      expectedWarning: {
        title: 'Make 3 annotations private?',
        message:
          'Are you sure you want to make "Test Name" a private group? 3 annotations that are publicly visible will become visible only to members of "Test Name".',
        confirmAction: 'Make annotations private',
      },
    },
    {
      // Warn when making annotations private (singular)
      oldType: 'open',
      newType: 'private',
      annotationCount: 1,
      expectedWarning: {
        title: 'Make 1 annotation private?',
        message:
          'Are you sure you want to make "Test Name" a private group? 1 annotation that is publicly visible will become visible only to members of "Test Name".',
        confirmAction: 'Make annotations private',
      },
    },
    {
      // Don't warn if there are no annotations
      oldType: 'open',
      newType: 'private',
      annotationCount: 0,
      expectedWarning: null,
    },
    {
      // Don't warn if the old and new types are both public
      oldType: 'open',
      newType: 'restricted',
      annotationCount: 3,
      expectedWarning: null,
    },
  ].forEach(({ oldType, newType, annotationCount, expectedWarning }) => {
    it('shows warning when changing group type between private and public', () => {
      if (oldType !== null) {
        config.context.group = {
          pubid: 'testid',
          name: 'Test Name',
          description: 'Test group description',
          link: 'https://example.com/groups/testid',
          type: oldType,
          num_annotations: annotationCount,
        };
      }

      const { wrapper } = createWrapper();
      setSelectedGroupType(wrapper, newType);

      if (expectedWarning) {
        const warning = wrapper.find('WarningDialog');
        assert.isTrue(warning.exists());
        assert.equal(warning.prop('title'), expectedWarning.title);
        assert.equal(warning.prop('message'), expectedWarning.message);
        assert.equal(
          warning.prop('confirmAction'),
          expectedWarning.confirmAction,
        );
      } else {
        assert.isFalse(wrapper.exists('WarningDialog'));
      }
    });
  });

  it('updates group type if change is confirmed', async () => {
    config.context.group = {
      pubid: 'testid',
      name: 'Test Name',
      description: 'Test group description',
      link: 'https://example.com/groups/testid',
      type: 'private',
      num_annotations: 3,
    };

    const { wrapper } = createWrapper();
    setSelectedGroupType(wrapper, 'open');

    const warning = wrapper.find('WarningDialog');
    act(() => warning.prop('onConfirm')());
    wrapper.update();

    assert.equal(getSelectedGroupType(wrapper), 'open');
  });

  it('does not update group type if change is canceled', async () => {
    config.context.group = {
      pubid: 'testid',
      name: 'Test Name',
      description: 'Test group description',
      link: 'https://example.com/groups/testid',
      type: 'private',
      num_annotations: 3,
    };

    const { wrapper } = createWrapper();
    setSelectedGroupType(wrapper, 'open');

    const warning = wrapper.find('WarningDialog');
    act(() => warning.prop('onCancel')());
    wrapper.update();

    assert.equal(getSelectedGroupType(wrapper), 'private');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});

async function assertInLoadingState(wrapper, inLoadingState) {
  await waitForElement(
    wrapper,
    `button[data-testid="button"][disabled=${inLoadingState}]`,
  );
  const state = wrapper.find('SaveStateIcon').prop('state');
  if (inLoadingState) {
    assert.equal(state, 'saving');
  } else {
    assert.notEqual(state, 'saving');
  }
}

function savedConfirmationShowing(wrapper) {
  return wrapper.find('SaveStateIcon').prop('state') === 'saved';
}
