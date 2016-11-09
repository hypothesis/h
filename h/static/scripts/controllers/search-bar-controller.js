'use strict';

var escapeHtml = require('escape-html');

var Controller = require('../base/controller');
var LozengeController = require('./lozenge-controller');
var AutosuggestDropdownController = require('./autosuggest-dropdown-controller');
var SearchTextParser = require('../util/search-text-parser');
var stringUtil = require('../util/string');

const FACET_TYPE = 'FACET';
const TAG_TYPE = 'TAG';
const MAX_SUGGESTIONS = 5;

/**
 * Controller for the search bar.
 */
class SearchBarController extends Controller {
  constructor(element) {
    super(element);

    this._input = this.refs.searchBarInput;
    this._lozengeContainer = this.refs.searchBarLozenges;


    var getTrimmedInputValue = () => {
      return this._input.value.trim();
    };

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

    let explanationList = [
      {
        matchOn: 'user',
        title: 'user:',
        explanation: 'search by username',
      },
      {
        matchOn: 'tag',
        title: 'tag:',
        explanation: 'search for annotations with a tag',
      },
      {
        matchOn: 'url',
        title: 'url:',
        explanation: 'see all annotations on a page',
      },
      {
        matchOn: 'group',
        title: 'group:',
        explanation: 'show annotations created in a group you are a member of',
      },
    ].map((item)=>{ return Object.assign(item, { type: FACET_TYPE}); });

    // tagSuggestions are made available by the scoped template data.
    // see search.html.jinja2 for definition
    const tagSuggestionJSON = document.querySelector('.js-tag-suggestions');
    let tagSuggestions = [];

    if(tagSuggestionJSON){
      try{
        tagSuggestions = JSON.parse(tagSuggestionJSON.innerHTML.trim());
      }catch(e){
        console.error('Could not parse .js-tag-suggestions JSON content', e);
      }
    }

    let tagsList = ((tagSuggestions) || []).map((item)=>{
      return Object.assign(item, {
        type: TAG_TYPE,
        title: escapeHtml(item.tag), // make safe
        matchOn: stringUtil.fold(stringUtil.normalize(item.tag)),
        usageCount: item.count || 0,
      });
    });


    this._suggestionsHandler = new AutosuggestDropdownController( this._input, {

      list: explanationList.concat(tagsList),

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

      listFilter: (list, currentInput)=>{

        currentInput = (currentInput || '').trim();

        let typeFilter = currentInput.indexOf('tag:') === 0 ? TAG_TYPE : FACET_TYPE;
        let inputFilter = stringUtil.fold(stringUtil.normalize(currentInput));

        if(typeFilter === TAG_TYPE){
          inputFilter = inputFilter.substr(/*'tag:' len*/4);

          // remove the initial quote for comparisons if it exists
          if(inputFilter[0] === '\'' || inputFilter[0] === '"'){
            inputFilter = inputFilter.substr(1);
          }
        }

        if(this.state.suggestionsType !== typeFilter){
          this.setState({
            suggestionsType: typeFilter,
          });
        }

        return list.filter((item)=>{
          return item.type === typeFilter && item.matchOn.toLowerCase().indexOf(inputFilter.toLowerCase()) >= 0;
        }).sort((a,b)=>{

          // this sort functions intention is to
          // sort partial matches as lower index match
          // value first. Then let natural sort of the
          // original list take effect if they have equal
          // index values or there is no current input value

          if (inputFilter){
            let aIndex = a.matchOn.indexOf(inputFilter);
            let bIndex = b.matchOn.indexOf(inputFilter);

            // match score
            if (aIndex > bIndex){
              return 1;
            } else if (aIndex < bIndex){
              return -1;
            }
          }


          // If we are filtering on tags, we need to arrange
          // by popularity
          if(typeFilter === TAG_TYPE){
            if(a.usageCount > b.usageCount){
              return -1;
            }else if(a.usageCount < b.usageCount) {
              return 1;
            }
          }

          return 0;

        }).slice(0, MAX_SUGGESTIONS);
      },

      onSelect: (itemSelected)=>{

        if (itemSelected.type === TAG_TYPE){
          let tagSelection = itemSelected.title;

          // wrap multi word phrases with quotes to keep
          // autosuggestions consistent with what user needs to do
          if(tagSelection.indexOf(' ') > -1){
            tagSelection = `"${tagSelection}"`;
          }

          addLozenge('tag:' + tagSelection);
          this._input.value = '';
        } else {
          this._input.value = itemSelected.title;
          setTimeout(()=>{
            this._input.focus();
          }, 0);
        }
        updateHiddenInput();
      },

    });

    this._input.addEventListener('keydown', onInputKeyDown);
    this._input.addEventListener('input', updateHiddenInput);
    lozengifyInput();
  }

  update(newState, prevState){

    if(!this._suggestionsHandler){
      return;
    }

    if(newState.suggestionsType !== prevState.suggestionsType){
      if(newState.suggestionsType === TAG_TYPE){
        this._suggestionsHandler.setHeader('Popular tags');
      }else {
        this._suggestionsHandler.setHeader('Narrow your search');
      }
    }

  }
}

module.exports = SearchBarController;
