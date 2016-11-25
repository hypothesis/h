'use strict';

// Template copied from navbar.html.jinja2
module.exports = `<div class="lozenge">
  <div class="lozenge__content">
    <span class="lozenge__facet-name" data-ref="facetName">
      {{ facetName }}:
    </span><!--
    !--><span class="lozenge__facet-value" data-ref="facetValue">
      {{ facetValue }}
    </span>
  </div>
  <button data-ref="deleteButton"
          class="lozenge__close"
          type="submit"
          name="delete_lozenge">
    <!-- Delete icon here !-->
  </button>
</div>`;
