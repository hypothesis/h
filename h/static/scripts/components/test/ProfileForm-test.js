import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import { LoginFormsConfig } from '../../config';
import ProfileForm from '../ProfileForm';

describe('ProfileForm', () => {
  let fakeConfig;

  beforeEach(() => {
    fakeConfig = {
      csrfToken: 'fake-csrf-token',
      features: {},
      form: {
        data: {
          display_name: '',
          description: '',
          location: '',
          link: '',
        },
        errors: {},
      },
    };
  });

  const getElements = wrapper => {
    return {
      form: wrapper.find('form[data-testid="form"]'),
      csrfInput: wrapper.find('input[name="csrf_token"]'),
      displayNameField: wrapper.find('TextField[name="display_name"]'),
      descriptionField: wrapper.find('TextField[name="description"]'),
      locationField: wrapper.find('TextField[name="location"]'),
      linkField: wrapper.find('TextField[name="link"]'),
      submitButton: wrapper.find('Button[data-testid="submit-button"]'),
    };
  };

  const createWrapper = () => {
    const wrapper = mount(
      <LoginFormsConfig.Provider value={fakeConfig}>
        <ProfileForm />
      </LoginFormsConfig.Provider>,
    );
    const elements = getElements(wrapper);
    return { wrapper, elements };
  };

  it('pre-fills form fields from form data', () => {
    fakeConfig.form.data = {
      display_name: 'John Doe',
      description: 'Software Developer',
      location: 'San Francisco, CA',
      link: 'https://johndoe.com',
    };

    const { elements } = createWrapper();
    const { displayNameField, descriptionField, locationField, linkField } =
      elements;

    assert.equal(
      displayNameField.prop('value'),
      fakeConfig.form.data.display_name,
    );
    assert.equal(
      descriptionField.prop('value'),
      fakeConfig.form.data.description,
    );
    assert.equal(locationField.prop('value'), fakeConfig.form.data.location);
    assert.equal(linkField.prop('value'), fakeConfig.form.data.link);
  });

  it('displays form errors', () => {
    fakeConfig.form.errors = {
      display_name: 'Display name is too long',
      description: 'Description is required',
      location: 'Invalid location',
      link: 'Must be a valid URL',
    };

    const { elements } = createWrapper();
    const { displayNameField, descriptionField, locationField, linkField } =
      elements;

    assert.equal(
      displayNameField.prop('fieldError'),
      fakeConfig.form.errors.display_name,
    );
    assert.equal(
      descriptionField.prop('fieldError'),
      fakeConfig.form.errors.description,
    );
    assert.equal(
      locationField.prop('fieldError'),
      fakeConfig.form.errors.location,
    );
    assert.equal(linkField.prop('fieldError'), fakeConfig.form.errors.link);
  });

  [
    { field: 'displayNameField', value: 'Jane Smith' },
    { field: 'descriptionField', value: 'Product Manager' },
    { field: 'locationField', value: 'New York, NY' },
    { field: 'linkField', value: 'https://janesmith.dev' },
  ].forEach(({ field, value }) => {
    it(`updates ${field} when input changes`, () => {
      const { wrapper, elements } = createWrapper();

      act(() => {
        elements[field].prop('onChangeValue')(value);
      });
      wrapper.update();
      const updatedElements = getElements(wrapper);

      assert.equal(updatedElements[field].prop('value'), value);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => createWrapper().wrapper }),
  );
});
