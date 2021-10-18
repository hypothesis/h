import { Controller } from '../base/controller';
import { setElementState } from '../util/dom';

export class CharacterLimitController extends Controller {
  constructor(element) {
    super(element);

    this.refs.characterLimitInput.addEventListener('input', () => {
      this.forceUpdate();
    });
    this.forceUpdate();
  }

  update() {
    const input = this.refs.characterLimitInput;
    const maxlength = parseInt(input.dataset.maxlength);
    const counter = this.refs.characterLimitCounter;
    counter.textContent = input.value.length + '/' + maxlength;
    setElementState(counter, { tooLong: input.value.length > maxlength });
    setElementState(this.refs.characterLimitCounter, { ready: true });
  }
}
