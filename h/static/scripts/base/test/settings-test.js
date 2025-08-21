import { settings } from '../../base/settings';

function createJSONScriptTag(obj, className) {
  const el = document.createElement('script');
  el.type = 'application/json';
  el.textContent = JSON.stringify(obj);
  el.classList.add(className);
  el.classList.add('js-settings-test');
  return el;
}

function removeJSONScriptTags() {
  const elements = document.querySelectorAll('.js-settings-test');
  for (let i = 0; i < elements.length; i++) {
    elements[i].parentNode.removeChild(elements[i]);
  }
}

describe('settings', () => {
  afterEach(removeJSONScriptTags);

  it('reads config from .js-hypothesis-settings <script> tags', () => {
    document.body.appendChild(
      createJSONScriptTag({ key: 'value' }, 'js-hypothesis-settings'),
    );
    assert.deepEqual(settings(document), { key: 'value' });
  });

  it('reads config from <script> tags with the specified class name', () => {
    document.body.appendChild(
      createJSONScriptTag({ foo: 'bar' }, 'js-custom-settings'),
    );
    assert.deepEqual(settings(document), {});
    assert.deepEqual(settings(document, 'js-custom-settings'), { foo: 'bar' });
  });

  it('merges settings from all config <script> tags', () => {
    document.body.appendChild(createJSONScriptTag({ a: 1 }, 'settings'));
    document.body.appendChild(createJSONScriptTag({ b: 2 }, 'settings'));
    assert.deepEqual(settings(document, 'settings'), { a: 1, b: 2 });
  });
});
