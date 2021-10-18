import syn from 'syn';

import { AutosuggestDropdownController } from '../../controllers/autosuggest-dropdown-controller';
import { unroll } from '../util';

// syn's move functionality does not fire
// mouseenter and mouseleave events.
const mouseMove = (() => {
  let _lastMovePos;

  return posObj => {
    if (_lastMovePos) {
      const prevEl = document.elementFromPoint(
        _lastMovePos.pageX,
        _lastMovePos.pageY
      );
      const leaveEvent = document.createEvent('Events');
      leaveEvent.initEvent('mouseleave', true, false);
      prevEl.dispatchEvent(leaveEvent);
    }

    _lastMovePos = posObj;

    const el = document.elementFromPoint(posObj.pageX, posObj.pageY);
    const enterEevent = document.createEvent('Events');
    enterEevent.initEvent('mouseenter', true, false);
    el.dispatchEvent(enterEevent);
  };
})();

function center(element) {
  const rect = element.getBoundingClientRect();
  return {
    pageX: rect.left + rect.width / 2,
    pageY: rect.top + rect.height / 2,
  };
}

describe('AutosuggestDropdownController', () => {
  describe('provides suggestions', () => {
    let container;
    let input;
    let form;

    const defaultConfig = {
      list: [
        {
          title: 'user:',
          explanation: 'search by username',
        },
        {
          title: 'tag:',
          explanation: 'search for annotations with a tag',
        },
        {
          title: 'url:',
          explanation: `search by URL<br>for domain level search
            add trailing /* eg. example.com/*`,
        },
        {
          title: 'group:',
          explanation:
            'show annotations created in a group you are a member of',
        },
      ],

      header: 'Some awesome header value',

      classNames: {
        container: 'the-container',
        header: 'the-header',
        list: 'the-list',
        item: 'an-item',
        activeItem: 'an-active-item',
      },

      renderListItem: listItem => {
        let itemContents = `<span class="a-title"> ${listItem.title} </span>`;

        if (listItem.explanation) {
          itemContents += `<span class="an-explanation"> ${listItem.explanation} </span>`;
        }

        return itemContents;
      },

      listFilter: function (list, currentInput) {
        currentInput = (currentInput || '').trim();

        return list.filter(item => {
          if (!currentInput) {
            return item;
          }
          return item.title.toLowerCase().indexOf(currentInput) >= 0;
        });
      },

      onSelect: function () {},
    };

    const isSuggestionContainerVisible = () => {
      const suggestionContainer = container.querySelector(
        '.' + defaultConfig.classNames.container
      );
      return suggestionContainer.classList.contains('is-open');
    };

    const getListItems = () => {
      const suggestionContainer = container.querySelector(
        '.' + defaultConfig.classNames.container
      );
      return suggestionContainer.querySelectorAll(
        '.' + defaultConfig.classNames.item
      );
    };

    const getCurrentActiveElements = () => {
      const list = container.querySelector('.' + defaultConfig.classNames.list);
      return list.querySelectorAll('.' + defaultConfig.classNames.activeItem);
    };

    beforeEach(() => {
      container = document.createElement('div');
      container.innerHTML = '<form><input id="input-el"/></form>';
      document.body.appendChild(container);
      input = document.getElementById('input-el');
      form = container.querySelector('form');
      form.onsubmit = sinon.spy();
    });

    afterEach(() => {
      document.body.removeChild(container);

      // clear up spies
      if ('restore' in defaultConfig.listFilter) {
        defaultConfig.listFilter.restore();
      }

      if ('restore' in defaultConfig.onSelect) {
        defaultConfig.onSelect.restore();
      }
    });

    it('should initialize the controller with correct dom', () => {
      assert.isTrue(form.childNodes.length === 1, 'baseline');

      new AutosuggestDropdownController(input, defaultConfig);

      assert.isFalse(
        form.childNodes.length === 1,
        'initializing should add container to dom'
      );

      const suggestionContainer = container.querySelector(
        '.' + defaultConfig.classNames.container
      );

      assert.isOk(suggestionContainer);
      assert.isOk(
        suggestionContainer.querySelector('.' + defaultConfig.classNames.header)
      );
      assert.isOk(
        suggestionContainer.querySelector('.' + defaultConfig.classNames.list)
      );
      assert.lengthOf(getListItems(), 4);

      assert.lengthOf(
        suggestionContainer.querySelectorAll('.a-title'),
        4,
        'reflects our rendering'
      );
      assert.lengthOf(
        suggestionContainer.querySelectorAll('.an-explanation'),
        4,
        'reflects our rendering'
      );
    });

    it('opens and closes based on focus status', done => {
      new AutosuggestDropdownController(input, defaultConfig);

      assert.isFalse(isSuggestionContainerVisible(), 'basline is hidden');

      syn.click(input, () => {
        assert.isTrue(isSuggestionContainerVisible(), 'focus should show');

        syn.click(document.body, () => {
          assert.isFalse(isSuggestionContainerVisible(), 'blur should hide');
          done();
        });
      });
    });

    it('changes suggestion container and item visibility on matching input', done => {
      const reduceSpy = sinon.spy(defaultConfig, 'listFilter');

      assert.equal(reduceSpy.callCount, 0);

      new AutosuggestDropdownController(input, defaultConfig);

      assert.equal(
        reduceSpy.callCount,
        1,
        'gets initial reduced list on initialize'
      );

      assert.lengthOf(getListItems(), 4);

      syn
        .click(input, () => {
          assert.equal(reduceSpy.callCount, 2, 'reduces on focus');
          assert.isTrue(isSuggestionContainerVisible(), 'focus show');
        })
        .type('u', () => {
          assert.lengthOf(getListItems(), 3);
          assert.equal(reduceSpy.callCount, 3, 'reduces on input');
        })
        .type('r', () => {
          assert.lengthOf(getListItems(), 1);
          assert.equal(reduceSpy.callCount, 4, 'reduces on input');

          assert.isTrue(isSuggestionContainerVisible(), 'still showing');
        })
        .type('x', () => {
          assert.lengthOf(getListItems(), 0);
          assert.equal(reduceSpy.callCount, 5, 'reduces on input');

          assert.isFalse(isSuggestionContainerVisible(), 'no match hide');
        })

        // backspace
        .type('\b', () => {
          assert.lengthOf(getListItems(), 1);
          assert.equal(reduceSpy.callCount, 6, 'reduces on input');

          assert.isTrue(isSuggestionContainerVisible(), 're match show');

          done();
        });
    });

    it('allows click selection', done => {
      const onSelectSpy = sinon.spy(defaultConfig, 'onSelect');

      assert.equal(onSelectSpy.callCount, 0);

      new AutosuggestDropdownController(input, defaultConfig);

      syn.click(input).type('t', () => {
        const items = getListItems();

        assert.lengthOf(items, 1);

        assert.isTrue(isSuggestionContainerVisible(), 'pre select show');

        syn.click(items[0], () => {
          assert.equal(onSelectSpy.callCount, 1);

          const selectedItem = onSelectSpy.args[0][0];

          assert.propertyVal(selectedItem, 'title', 'tag:');
          assert.propertyVal(
            selectedItem,
            'explanation',
            'search for annotations with a tag'
          );

          assert.isFalse(isSuggestionContainerVisible(), 'post select hide');

          done();
        });
      });
    });

    const navigationExpectations = [
      { travel: '[down]', selectedIndex: 0 },
      { travel: '[up]', selectedIndex: 3 },
      { travel: '[down][up]', selectedIndex: -1 },
      { travel: '[up][down]', selectedIndex: -1 },
      { travel: '[down][down][down][down]', selectedIndex: 3 },
      { travel: '[down][down][down][down][down]', selectedIndex: -1 },
      { travel: '[up][up][up][up]', selectedIndex: 0 },
      { travel: '[up][up][up][up][up]', selectedIndex: -1 },
      {
        travel: '[up][down][up][down][down][down][down][up]',
        selectedIndex: 1,
      },
    ];

    unroll(
      'allows keyboard navigation',
      (done, fixture) => {
        new AutosuggestDropdownController(input, defaultConfig);

        const list = container.querySelector(
          '.' + defaultConfig.classNames.list
        );

        syn.click(input).type(fixture.travel, () => {
          const active = getCurrentActiveElements();
          if (fixture.selectedIndex === -1) {
            assert.lengthOf(active, 0);
          } else {
            assert.isTrue(
              list.childNodes[fixture.selectedIndex].classList.contains(
                defaultConfig.classNames.activeItem
              )
            );
            assert.lengthOf(active, 1);
          }
          done();
        });
      },
      navigationExpectations
    );

    it('persists active navigation through list filter', done => {
      new AutosuggestDropdownController(input, defaultConfig);

      const list = container.querySelector('.' + defaultConfig.classNames.list);
      syn
        .click(input)
        .type('[down][down]', () => {
          assert.isTrue(
            list.childNodes[1].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );
          assert.equal(
            list.childNodes[1].querySelector('.a-title').textContent.trim(),
            defaultConfig.list[1].title
          );
        })
        .type('t', () => {
          assert.isTrue(
            list.childNodes[0].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );
          assert.equal(
            list.childNodes[0].querySelector('.a-title').textContent.trim(),
            defaultConfig.list[1].title
          );
          done();
        });
    });

    it('allows keyboard selection', done => {
      const onSelectSpy = sinon.spy(defaultConfig, 'onSelect');

      assert.equal(onSelectSpy.callCount, 0);

      new AutosuggestDropdownController(input, defaultConfig);

      syn.click(input).type('[down][down][enter]', () => {
        assert.equal(onSelectSpy.callCount, 1);

        const selectedItem = onSelectSpy.args[0][0];

        assert.propertyVal(selectedItem, 'title', 'tag:');
        assert.propertyVal(
          selectedItem,
          'explanation',
          'search for annotations with a tag'
        );

        assert.isFalse(
          form.onsubmit.called,
          'should not submit the form on enter'
        );

        done();
      });
    });

    it('can hover items', done => {
      new AutosuggestDropdownController(input, defaultConfig);

      const list = container.querySelector('.' + defaultConfig.classNames.list);

      syn.click(input, () => {
        mouseMove(center(list.childNodes[1]));

        assert.lengthOf(getCurrentActiveElements(), 1);
        assert.isTrue(
          list.childNodes[1].classList.contains(
            defaultConfig.classNames.activeItem
          )
        );

        mouseMove(center(list.childNodes[2]));

        assert.lengthOf(getCurrentActiveElements(), 1);
        assert.isTrue(
          list.childNodes[2].classList.contains(
            defaultConfig.classNames.activeItem
          )
        );

        mouseMove(center(input));
        assert.lengthOf(getCurrentActiveElements(), 0);

        done();
      });
    });

    it('correctly sets active elements when swapping between keyboard and mouse setting', done => {
      new AutosuggestDropdownController(input, defaultConfig);

      const list = container.querySelector('.' + defaultConfig.classNames.list);

      syn
        .click(input, () => {
          mouseMove(center(list.childNodes[2]));

          assert.lengthOf(getCurrentActiveElements(), 1);
          assert.isTrue(
            list.childNodes[2].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );
        })
        .type('[down]', () => {
          assert.lengthOf(getCurrentActiveElements(), 1);
          assert.isTrue(
            list.childNodes[3].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );
        })
        .type('[up][up][up]', () => {
          assert.lengthOf(getCurrentActiveElements(), 1);
          assert.isTrue(
            list.childNodes[0].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );

          mouseMove(center(list.childNodes[2]));

          assert.lengthOf(getCurrentActiveElements(), 1);
          assert.isTrue(
            list.childNodes[2].classList.contains(
              defaultConfig.classNames.activeItem
            )
          );

          done();
        });
    });
  });
});
