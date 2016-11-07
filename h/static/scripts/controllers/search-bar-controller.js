'use strict';

var Controller = require('../base/controller');
var LozengeController = require('./lozenge-controller');
var AutosuggestDropdownController = require('./autosuggest-dropdown-controller');
var SearchTextParser = require('../util/search-text-parser');

/**
 * Controller for the search bar.
 */
class SearchBarController extends Controller {
  constructor(element) {
    super(element);

    this._input = this.refs.searchBarInput;
    this._lozengeContainer = this.refs.searchBarLozenges;

    let explanationList = [
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
        explanation: 'see all annotations on a page',
      },
      {
        title: 'group:',
        explanation: 'show annotations created in a group you are a member of',
      },
    ];

    var selectFacet = facet => {
      this._input.value = facet;

      setTimeout(()=>{
        this._input.focus();
      }, 0);
    };


    var getTrimmedInputValue = () => {
      return this._input.value.trim();
    };

    new AutosuggestDropdownController( this._input, {

      list: explanationList,

      header: 'Narrow your search',

      classNames: {
        container: 'search-bar__dropdown-menu-container',
        header: 'search-bar__dropdown-menu-header',
        list: 'search-bar__dropdown-menu',
        item: 'search-bar__dropdown-menu-item',
        activeItem: 'js-search-bar-dropdown-menu-item--active',
      },

      renderListItem: (listItem)=>{

        let itemContents = `<span class="search-bar__dropdown-menu-title"> ${listItem.title} </span>`;

        if (listItem.explanation){
          itemContents += `<span class="search-bar__dropdown-menu-explanation"> ${listItem.explanation} </span>`;
        }

        return itemContents;
      },

      listFilter: function(list, currentInput){

        currentInput = (currentInput || '').trim();

        return list.filter((item)=>{

          if (!currentInput){
            return item;
          } else if (currentInput.indexOf(':') > -1) {
            return false;
          }
          return item.title.toLowerCase().indexOf(currentInput) >= 0;

        }).sort((a,b)=>{

          // this sort functions intention is to
          // sort partial matches as lower index match
          // value first. Then let natural sort of the
          // original list take effect if they have equal
          // index values or there is no current input value

          if (!currentInput){
            return 0;
          }

          let aIndex = a.title.indexOf(currentInput);
          let bIndex = b.title.indexOf(currentInput);

          if (aIndex > bIndex){
            return 1;
          } else if (aIndex < bIndex){
            return -1;
          }
          return 0;
        });
      },

      onSelect: (itemSelected)=>{
        selectFacet(itemSelected.title);
      },

    });


    /**
     * Insert a hidden <input> with an empty value into the search <form>.
     *
     * The name="q" attribute is moved from the visible <input> on to the
     * hidden <input> so that when the <form> is submitted it's the value of
     * the _hidden_ input, not the visible one, that is submitted as the
     * q parameter.
     *
     */
    var insertHiddenInput = () => {
      var hiddenInput = document.createElement('input');
      hiddenInput.type = 'hidden';

      // When JavaScript isn't enabled this._input is submitted to the server
      // as the q param. With JavaScript we submit hiddenInput instead.
      hiddenInput.name = this._input.name;
      this._input.removeAttribute('name');

      this.refs.searchBarForm.appendChild(hiddenInput);
      return hiddenInput;
    };

    /**
     * Update the value of the hidden input.
     *
     * Update the value of the hidden input based on the contents of any
     * lozenges and any remaining text in the visible input.
     *
     * This should be called whenever a lozenge is added to or removed from
     * the DOM, and whenever the text in the visible input changes.
     *
     */
    var updateHiddenInput = () => {
      let newValue = '';
      Array.from(this._lozengeContainer.querySelectorAll('.js-lozenge__content')).forEach((loz) => {
        newValue = newValue + loz.textContent + ' ';
      });
      this._hiddenInput.value = (newValue + getTrimmedInputValue()).trim();
    };

    /**
     * Creates a lozenge and sets the content string to the
     * content provided and executes the delete callback when
     * the lozenge is deleted.
     *
     * @param {string} content The search term
     */
    var addLozenge = content => {
      var deleteCallback = () => {
        Array.from(this._lozengeContainer.querySelectorAll('.js-lozenge')).forEach(function(loz) {
          loz.classList.add('is-disabled');
        });
        updateHiddenInput();
        this.refs.searchBarForm.submit();
      };

      new LozengeController(
        this._lozengeContainer,
        {
          content: content,
          deleteCallback: deleteCallback,
        }
      );
    };

    /**
     * Create lozenges for the search query terms already in the input field on
     * page load.
     */
    var lozengifyInput = () => {
      var {lozengeValues, incompleteInputValue} = SearchTextParser.getLozengeValues(this._input.value);
      lozengeValues.forEach(addLozenge);
      this._input.value = incompleteInputValue;
      this._input.style.visibility = 'visible';
      updateHiddenInput();
    };

    var onInputKeyDown = event => {
      const SPACE_KEY_CODE = 32;

      if (event.keyCode === SPACE_KEY_CODE) {
        const word = getTrimmedInputValue();
        if (SearchTextParser.shouldLozengify(word)) {
          event.preventDefault();
          addLozenge(word);
          this._input.value = '';
          updateHiddenInput();
        }
      }
    };

    this._hiddenInput = insertHiddenInput(this.refs.searchBarForm);

    this._input.addEventListener('keydown', onInputKeyDown);
    this._input.addEventListener('input', updateHiddenInput);
    lozengifyInput();
  }
}

module.exports = SearchBarController;
