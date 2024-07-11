import { useId } from 'preact/hooks';

import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

function Star() {
  return <span className="text-brand">*</span>;
}

function CharacterCounter({
  value,
  limit,
  testid,
}: {
  value: number;
  limit: number;
  testid: string;
}) {
  return (
    <div className="flex">
      <div className="grow" />
      <span data-testid={testid}>
        {value}/{limit}
      </span>
    </div>
  );
}

function Label({
  htmlFor,
  text,
  required,
}: {
  htmlFor: string;
  text: string;
  required?: boolean;
}) {
  return (
    <label htmlFor={htmlFor}>
      {text}
      {required ? <Star /> : null}
    </label>
  );
}

export default function CreateGroupForm() {
  const nameId = useId();
  const descriptionId = useId();

  return (
    <div className="text-grey-6 text-sm/tight">
      <h1 className="mt-14 mb-8 text-grey-7 text-xl/none">
        Create a new private group
      </h1>

      <form>
        <div className="mb-4">
          <Label htmlFor={nameId} text="Name" required />
          <Input id={nameId} autofocus autocomplete="off" required />
          <CharacterCounter
            value={0}
            limit={25}
            testid="character-counter-name"
          />
        </div>

        <div className="mb-4">
          <Label htmlFor={descriptionId} text="Description" />
          <Textarea id={descriptionId} classes="h-24" />
          <CharacterCounter
            value={0}
            limit={250}
            testid="character-counter-description"
          />
        </div>

        <div className="flex">
          <div className="grow" />
          <Button variant="primary">Create group</Button>
        </div>
      </form>

      <footer className="mt-14 pt-4 border-t border-t-text-grey-6">
        <div className="flex">
          <div className="grow" />
          <Star />
          &nbsp;Required
        </div>
      </footer>
    </div>
  );
}
