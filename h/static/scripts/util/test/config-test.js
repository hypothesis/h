import { findContainer, readConfig } from '../config';

describe('readConfig', () => {
  let expectedConfig;
  let configEl;

  beforeEach(() => {
    expectedConfig = {
      styles: ['/static/foo.css'],
    };
    configEl = document.createElement('script');
    configEl.className = 'js-config';
    configEl.type = 'application/json';
    configEl.textContent = JSON.stringify(expectedConfig);
    document.body.appendChild(configEl);
  });

  afterEach(() => {
    configEl.remove();
  });

  it('should throw if the .js-config object is missing', () => {
    configEl.remove();
    assert.throws(() => {
      readConfig();
    }, 'Failed to parse frontend configuration');
  });

  it('should throw if the config cannot be parsed', () => {
    configEl.textContent = 'not valid JSON';
    assert.throws(() => {
      readConfig();
    }, 'Failed to parse frontend configuration');
  });

  it('should return the parsed configuration', () => {
    const config = readConfig();
    assert.deepEqual(config, expectedConfig);
  });
});

describe('findContainer', () => {
  let container;

  beforeEach(() => {
    container = document.createElement('div');
    container.id = 'test-form';
    document.body.append(container);
  });

  afterEach(() => {
    container.remove();
  });

  it('returns container', () => {
    assert.equal(findContainer('#test-form'), container);
  });

  it('throws if container is missing', () => {
    assert.throws(
      () => findContainer('#wrong-id'),
      'Unable to render UI because container "#wrong-id" was not found',
    );
  });
});
