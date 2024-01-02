import { assert } from 'chai';
import sinon from 'sinon';

// Expose the sinon assertions.
sinon.assert.expose(assert, { prefix: null });

// Expose these globally, to avoid dependency on outdated karma-chai and
// karma-sinon plugins
globalThis.assert = assert;
globalThis.sinon = sinon;
