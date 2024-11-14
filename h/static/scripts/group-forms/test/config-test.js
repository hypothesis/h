import { readConfig } from '../config';

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
