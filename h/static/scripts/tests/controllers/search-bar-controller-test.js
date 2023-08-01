import syn from 'syn';

import { LozengeController } from '../../controllers/lozenge-controller';
import { SearchBarController } from '../../controllers/search-bar-controller';
import { cloneTemplate } from '../../util/dom';
import { unroll } from '../util';
import lozengeTemplate from './lozenge-template';
import * as util from './util';

/**
 * Return the search terms displayed by all lozenges in a search bar.
 *
 * @param {SearchBarController} ctrl
 * @return {string[]}
 */
const getLozengeValues = ctrl => {
  return Array.from(
    ctrl.refs.searchBarLozenges.querySelectorAll('.lozenge'),
  ).map(el => {
    const facetName = el.querySelector('.lozenge__facet-name').textContent;
    const facetValue = el.querySelector('.lozenge__facet-value').textContent;
    return facetName + facetValue;
  });
};

describe('SearchBarController', () => {
  let lozengeTemplateEl;

  before(() => {
    lozengeTemplateEl = document.createElement('template');
    lozengeTemplateEl.id = 'lozenge-template';
    lozengeTemplateEl.innerHTML = lozengeTemplate;
    document.body.appendChild(lozengeTemplateEl);
  });

  after(() => {
    lozengeTemplateEl.remove();
  });

  describe('Autosuggest', () => {
    let testEl;
    let input;
    let dropdown;
    let ctrl;
    const TEMPLATE = `
      <div>
        <form data-ref="searchBarForm">
          <div class="search-bar__lozenges" data-ref="searchBarLozenges">
          </div>
          <input data-ref="searchBarInput" class="search-bar__input" name="q" />
        </form>
      </div>
    `;

    const getItemTitles = function () {
      return Array.from(
        dropdown.querySelectorAll('.search-bar__dropdown-menu-title'),
      ).map(node => {
        return node.textContent.trim();
      });
    };

    const setup = function () {
      testEl = document.createElement('div');
      testEl.innerHTML = TEMPLATE;
      document.body.appendChild(testEl);

      ctrl = new SearchBarController(testEl);

      input = ctrl.refs.searchBarInput;
      dropdown = input.nextSibling;
    };

    const teardown = function () {
      document.body.removeChild(testEl);
      const tagsJSON = document.querySelector('.js-tag-suggestions');
      if (tagsJSON) {
        tagsJSON.remove();
      }

      const groupsJSON = document.querySelector('.js-group-suggestions');
      if (groupsJSON) {
        groupsJSON.remove();
      }
    };

    const addTagSuggestions = function () {
      const suggestions = [
        {
          tag: 'aaaa',
          count: 1,
        },
        {
          tag: 'aaab',
          count: 1,
        },
        {
          tag: 'aaac',
          count: 4,
        },
        {
          tag: 'aaad',
          count: 3,
        },
        {
          tag: 'aaae',
          count: 1,
        },
        {
          tag: 'aadf',
          count: 3,
        },
        {
          tag: 'aaag',
          count: 2,
        },
        {
          tag: 'multi word',
          count: 1,
        },
        {
          tag: 'effort',
          count: 1,
        },
      ];

      const tagsScript = document.createElement('script');
      tagsScript.innerHTML = JSON.stringify(suggestions);
      tagsScript.className = 'js-tag-suggestions';
      document.body.appendChild(tagsScript);
    };

    const addGroupSuggestions = function () {
      const suggestions = [
        {
          name: 'aaac',
          pubid: 'pid1',
        },
        {
          name: 'aaab',
          pubid: 'pid2',
        },
        {
          name: 'aaaa',
          pubid: 'pid3',
        },
        {
          name: 'aaae',
          pubid: 'pid4',
        },
        {
          name: 'aaad',
          pubid: 'pid5',
        },
        {
          name: 'aadf',
          pubid: 'pid6',
        },
        {
          name: 'aaag',
          pubid: 'pid7',
        },
        {
          name: 'multi word',
          pubid: 'pid8',
        },
        {
          name: 'effort',
          pubid: 'pid9',
        },
        {
          name: '<*>Haskell fans<*>',
          pubid: 'pid10',
        },
      ];

      const groupsScript = document.createElement('script');
      groupsScript.innerHTML = JSON.stringify(suggestions);
      groupsScript.className = 'js-group-suggestions';
      document.body.appendChild(groupsScript);
    };

    beforeEach(setup);
    afterEach(teardown);

    it('uses autosuggestion for initial facets', done => {
      assert.isFalse(dropdown.classList.contains('is-open'));

      syn.click(input, () => {
        assert.isTrue(dropdown.classList.contains('is-open'));

        assert.deepEqual(getItemTitles(), ['user:', 'tag:', 'url:', 'group:']);

        done();
      });
    });

    it('it filters and updates input with autosuggested facet selection', done => {
      syn
        .click(input, () => {
          assert.notOk(input.value, 'baseline no value in input');
        })
        .type('r[down][enter]', () => {
          assert.equal(input.value, 'url:');
          done();
        });
    });

    it('allows submitting the form dropdown is open but has no selected value', done => {
      const form = testEl.querySelector('form');
      const submit = sinon.stub(form, 'submit');

      syn
        .click(input)
        .type('test[space]', () => {
          assert.isTrue(dropdown.classList.contains('is-open'));
        })
        .type('[enter]', () => {
          assert.equal(
            testEl.querySelector('input[type=hidden]').value,
            'test',
          );
          assert.isTrue(submit.calledOnce);
          done();
        });
    });

    describe('it allows group value suggestions', () => {
      beforeEach(() => {
        // we need to setup the env vars before invoking controller
        teardown();
        addGroupSuggestions();
        setup();

        sinon.stub(testEl.querySelector('form'), 'submit');
      });

      unroll(
        'shows group suggestions',
        (done, fixture) => {
          syn
            .click(input)
            .type(fixture.text, () => {
              assert.isTrue(dropdown.classList.contains('is-open'));

              const titles = getItemTitles();

              assert.lengthOf(
                titles,
                5,
                'we should be enforcing the 5 item max',
              );
            })
            .type(
              '[backspace][backspace][backspace][backspace][backspace][backspace]',
              () => {
                assert.deepEqual(
                  getItemTitles(),
                  ['user:', 'tag:', 'url:', 'group:'],
                  'group suggestions go away as facet is removed',
                );
                done();
              },
            );
        },
        [{ text: 'group:' }, { text: 'Group:' }, { text: 'GROUP:' }],
      );

      it('orders groups by earliest value match first', done => {
        syn
          .click(input)
          .type('group:', () => {
            assert.deepEqual(
              getItemTitles(),
              ['aaac', 'aaab', 'aaaa', 'aaae', 'aaad'],
              'default ordering based on original order with no input',
            );
          })
          .type('aad', () => {
            assert.deepEqual(
              getItemTitles(),
              ['aadf', 'aaad'],
              'sorting by indexof score with some input',
            );
            done();
          });
      });

      it('supports multi word matching', done => {
        syn
          .click(input)
          .type('group:"mul', () => {
            assert.deepEqual(
              getItemTitles(),
              ['multi word'],
              'supports matching on a double quote initial input',
            );
          })
          .type("[backspace][backspace][backspace][backspace]'mul", () => {
            assert.deepEqual(
              getItemTitles(),
              ['multi word'],
              'supports matching on a single quote initial input',
            );
            done();
          });
      });

      it('handles filtering matches with unicode', done => {
        syn.click(input).type('group:éf', () => {
          assert.deepEqual(
            getItemTitles(),
            ['effort'],
            'matches éffort with unicode value',
          );
          done();
        });
      });

      it('sets input and display friendly name value', done => {
        syn
          .click(input)
          .type('group:"mul[down][enter]', () => {
            assert.equal(
              testEl.querySelector('input[type=hidden]').value.trim(),
              'group:pid8',
              'pubid should be added to the hidden input',
            );
            assert.deepEqual(
              getLozengeValues(ctrl),
              ['group:"multi word"'],
              'adds and wraps multi word with quotes',
            );
          })
          .type('group:a[down][enter]', () => {
            assert.equal(
              testEl.querySelector('input[type=hidden]').value.trim(),
              'group:pid8 group:pid1',
              'pubid should be added to the hidden input',
            );
            assert.deepEqual(
              getLozengeValues(ctrl),
              ['group:"multi word"', 'group:aaac'],
              'adds single word as is to lozenge',
            );
            done();
          });
      });

      it('matches escaped values', done => {
        syn.click(input).type('group:<[down][enter]', () => {
          assert.equal(
            testEl.querySelector('input[type=hidden]').value.trim(),
            'group:pid10',
            'pubid should be added to the hidden input',
          );
          assert.deepEqual(
            getLozengeValues(ctrl),
            ['group:"<*>Haskell fans<*>"'],
            'adds and wraps multi word with quotes',
          );
          done();
        });
      });
    });

    describe('it allows tag value suggestions', () => {
      beforeEach(() => {
        // we need to setup the env vars before invoking controller
        teardown();
        addTagSuggestions();
        setup();

        sinon.stub(testEl.querySelector('form'), 'submit');
      });

      unroll(
        'shows tag suggestions',
        (done, fixture) => {
          syn
            .click(input)
            .type(fixture.text, () => {
              assert.isTrue(dropdown.classList.contains('is-open'));

              const titles = getItemTitles();

              assert.lengthOf(
                titles,
                5,
                'we should be enforcing the 5 item max',
              );
            })
            .type('[backspace][backspace][backspace][backspace]', () => {
              assert.deepEqual(
                getItemTitles(),
                ['user:', 'tag:', 'url:', 'group:'],
                'tags go away as facet is removed',
              );
              done();
            });
        },
        [{ text: 'tag:' }, { text: 'Tag:' }, { text: 'TAG:' }],
      );

      it('orders tags by priority and indexOf score', done => {
        syn
          .click(input)
          .type('tag:', () => {
            assert.deepEqual(
              getItemTitles(),
              ['aaac', 'aaad', 'aadf', 'aaag', 'aaaa'],
              'default ordering based on priority',
            );
          })
          .type('aad', () => {
            assert.deepEqual(
              getItemTitles(),
              ['aadf', 'aaad'],
              'sorting by indexof score with equal priority',
            );
            done();
          });
      });

      it('matches on multi word searches', done => {
        syn
          .click(input)
          .type('tag:"mul', () => {
            assert.deepEqual(
              getItemTitles(),
              ['multi word'],
              'supports matching on a double quote initial input',
            );
          })
          .type("[backspace][backspace][backspace][backspace]'mul", () => {
            assert.deepEqual(
              getItemTitles(),
              ['multi word'],
              'supports matching on a single quote initial input',
            );
          })
          .type('[down][enter][enter]', () => {
            assert.equal(
              testEl.querySelector('input[type=hidden]').value.trim(),
              'tag:"multi word"',
              'selecting a multi word tag should wrap with quotes',
            );
            done();
          });
      });

      it('handles filtering matches with unicode', done => {
        syn.click(input).type('tag:éf', () => {
          assert.deepEqual(
            getItemTitles(),
            ['effort'],
            'matches éffort with unicode value',
          );
          done();
        });
      });
    });
  });

  describe('Lozenges', () => {
    let ctrl;

    afterEach(() => {
      if (ctrl) {
        ctrl.element.remove();
        ctrl = null;
      }
    });

    /**
     * Make a <form> with the SearchBarController enhancement applied and
     * return the various parts of the component.
     *
     */
    function component(value, lozengeContent) {
      value = value || '';
      lozengeContent = lozengeContent || '';
      const template = `
        <div>
          <form data-ref="searchBarForm">
            <div class="search-bar__lozenges" data-ref="searchBarLozenges">${lozengeContent}</div>
            <input data-ref="searchBarInput" class="search-bar__input" name="q" value="${value}">
          </form>
        </div>
      `.trim();

      ctrl = util.setupComponent(document, template, SearchBarController);

      // Stub the submit method so it doesn't actually do a full page reload.
      ctrl.refs.searchBarForm.submit = sinon.stub();

      return {
        ctrl: ctrl,
        hiddenInput: ctrl.element.querySelector('input[type="hidden"]'),
        input: ctrl.refs.searchBarInput,
      };
    }

    /**
     * Return all of the given controller's lozenge elements (if any).
     *
     */
    function getLozenges(ctrl) {
      return ctrl.refs.searchBarLozenges.querySelectorAll('.js-lozenge');
    }

    it('should create lozenges for existing query terms in the input on page load', () => {
      const { ctrl } = component('foo');

      assert.deepEqual(getLozengeValues(ctrl), ['foo']);
    });

    it('inserts a hidden input on init', () => {
      const { hiddenInput } = component();

      assert.notEqual(hiddenInput, null);
    });

    it('removes the name="q" attribute from the input on init', () => {
      const { input } = component();

      assert.isFalse(input.hasAttribute('name'));
    });

    it('adds the name="q" attribute to the hidden input on init', () => {
      const { hiddenInput } = component();

      assert.equal(hiddenInput.getAttribute('name'), 'q');
    });

    it('leaves the hidden input empty on init if the visible input is empty', () => {
      const { hiddenInput } = component();

      assert.equal(hiddenInput.value, '');
    });

    it('copies lozengifiable text from the input into the hidden input on init', () => {
      const { hiddenInput } = component('these are my tag:lozenges');

      assert.equal(hiddenInput.value, 'these are my tag:lozenges');
    });

    it('copies unlozengifiable text from the input into the hidden input on init', () => {
      const { hiddenInput } = component("group:'unclosed quotes");

      assert.equal(hiddenInput.value, "group:'unclosed quotes");
    });

    it('copies lozengifiable and unlozengifiable text from the input into the hidden input on init', () => {
      const { hiddenInput } = component(
        "these are my tag:lozenges group:'unclosed quotes",
      );

      assert.equal(
        hiddenInput.value,
        "these are my tag:lozenges group:'unclosed quotes",
      );
    });

    it('updates the value of the hidden input as text is typed into the visible input', () => {
      const { input, hiddenInput } = component('initial text');

      input.value = 'new text'; // This is just "new text" and not
      // "initial text new text" because the
      // "initial text" will have been moved into
      // lozenges.
      input.dispatchEvent(new Event('input'));

      assert.equal(hiddenInput.value, 'initial text new text');
    });

    it('updates the value of the hidden input as unlozengifiable text is typed into the visible input', () => {
      const { input, hiddenInput } = component("group:'unclosed quotes");

      input.value = "group:'unclosed quotes still unclosed";
      input.dispatchEvent(new Event('input'));

      assert.equal(hiddenInput.value, "group:'unclosed quotes still unclosed");
    });

    it('updates the value of the hidden input when a lozenge is deleted', () => {
      const { ctrl, hiddenInput } = component('foo bar');

      const lozenge = getLozenges(ctrl)[0];
      lozenge.controllers[0].options.deleteCallback();

      assert.equal(hiddenInput.value, 'bar');
    });

    it('should not create a lozenge for incomplete query strings in the input on page load', () => {
      const { ctrl, input } = component("'bar");

      assert.equal(getLozenges(ctrl).length, 0);
      assert.equal(input.value, "'bar");
    });

    it('should create a lozenge when the user presses space and there are no incomplete query strings in the input', done => {
      const { ctrl, input } = component('foo');

      syn
        .click(input)
        .type('gar')
        .type('[space]', () => {
          assert.deepEqual(getLozengeValues(ctrl), ['foo', 'gar']);
          done();
        });
    });

    it('should create a lozenge when the user completes a previously incomplete query string and then presses the space key', done => {
      const { ctrl, input } = component("'bar gar'");

      syn
        .click(input)
        .type(" gar'")
        .type('[space]', () => {
          assert.deepEqual(getLozengeValues(ctrl), ["'bar gar'"]);
          done();
        });
    });

    it('should not create a lozenge when the user does not completes a previously incomplete query string and presses the space key', done => {
      const { ctrl, input } = component("'bar");

      // Move cursor to end of field.
      input.selectionStart = input.value.length;

      syn
        .click(input)
        .type('[space]')
        .type('gar')
        .type('[space]', () => {
          const lozenges = getLozenges(ctrl);
          assert.equal(lozenges.length, 0);
          assert.equal(input.value, "'bar gar ");
          done();
        });
    });

    describe('mapping initial input value to proper group lozenge and input values', () => {
      let groupsScript;

      beforeEach(() => {
        const suggestions = [
          {
            name: 'abc 123',
            pubid: 'pid124',
          },
        ];

        groupsScript = document.createElement('script');
        groupsScript.innerHTML = JSON.stringify(suggestions);
        groupsScript.className = 'js-group-suggestions';
        document.body.appendChild(groupsScript);
      });

      afterEach(() => {
        groupsScript.remove();
      });

      it('should map an initial group name to proper group pubid input value', () => {
        const { input, hiddenInput } = component("group:'abc 123'");

        assert.deepEqual(getLozengeValues(ctrl), ['group:"abc 123"']);
        assert.equal(input.value, '');
        assert.equal(hiddenInput.value, 'group:pid124');
      });

      it('should map an initial group pubid to proper group name lozenge value', () => {
        const { input, hiddenInput } = component('group:pid124');

        assert.deepEqual(getLozengeValues(ctrl), ['group:"abc 123"']);
        assert.equal(input.value, '');
        assert.equal(hiddenInput.value, 'group:pid124');
      });

      it('places lozenges as first elements in container', done => {
        const template = `
            <div>
              <form data-ref="searchBarForm">
                <div class="search-bar__lozenges" data-ref="searchBarLozenges">
                    <input data-ref="searchBarInput" class="search-bar__input" name="q" value="">
                </div>
              </form>
            </div>
          `.trim();

        const ctrl = util.setupComponent(
          document,
          template,
          SearchBarController,
        );

        // Stub the submit method so it doesn't actually do a full page reload.
        ctrl.refs.searchBarForm.submit = sinon.stub();

        const container = ctrl.element.querySelector('.search-bar__lozenges');
        const input = ctrl.refs.searchBarInput;

        let currentChildrenCount = container.children.length;

        syn.click(input).type('foo[space]', () => {
          currentChildrenCount += 1;

          assert.lengthOf(
            container.children,
            currentChildrenCount,
            'lozenge add should be added as a child',
          );

          assert.ok(
            container.children[0].classList.contains('lozenge'),
            'should be set as first child',
          );

          done();
        });
      });

      it('places lozenges after any initial lozenges', done => {
        const template = `
            <div>
              <form data-ref="searchBarForm">
                <div class="search-bar__lozenges" data-ref="searchBarLozenges">
                    <input data-ref="searchBarInput" class="search-bar__input" name="q" value="">
                </div>
              </form>
            </div>
          `.trim();

        const ctrl = util.setupComponent(
          document,
          template,
          SearchBarController,
        );

        // Stub the submit method so it doesn't actually do a full page reload.
        ctrl.refs.searchBarForm.submit = sinon.stub();

        const container = ctrl.element.querySelector('.search-bar__lozenges');

        const lozengeEl = cloneTemplate(lozengeTemplateEl);
        new LozengeController(lozengeEl, { content: 'seeded' });

        container.insertBefore(lozengeEl, container.firstChild);

        const input = ctrl.refs.searchBarInput;

        let currentChildrenCount = container.children.length;

        syn.click(input).type('foo[space]', () => {
          currentChildrenCount += 1;

          assert.lengthOf(container.children, currentChildrenCount);

          assert.ok(container.children[0].classList.contains('lozenge'));
          assert.ok(container.children[1].classList.contains('lozenge'));

          assert.deepEqual(getLozengeValues(ctrl), ['seeded', 'foo']);

          done();
        });
      });
    });
  });
});
