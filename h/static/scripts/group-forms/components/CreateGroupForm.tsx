import { useId } from 'preact/hooks';

import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

export default function CreateGroupForm() {
  const nameId = useId();
  const descriptionId = useId();

  return (
    <div className="text-grey-6 text-sm/tight">
      <h1 className="mt-[55px] mb-[30px] text-grey-7 text-xl/none">
        Create a new private group
      </h1>

      <form>
        <div className="mb-[15px]">
          <Label htmlFor={nameId} text={'Name'} required={true} />
          <Input id={nameId} autofocus autocomplete="off" required />
          <CharacterCounter value={0} limit={25} />
        </div>

        <div className="mb-[15px]">
          <Label
            htmlFor={descriptionId}
            text={'Description'}
            required={false}
          />
          <Textarea id={descriptionId} />
          <CharacterCounter value={0} limit={250} />
        </div>

        <div className="flex">
          <div className="grow" />
          <Button variant="primary">Create group</Button>
        </div>
      </form>

      <footer className="mt-[50px] pt-[15px] border-t border-t-text-grey-6">
        <div className="flex">
          <div className="grow" />
          <span className="text-brand">*</span> Required
        </div>
      </footer>
    </div>
  );
}

function CharacterCounter({ value, limit }: { value: number; limit: number }) {
  return (
    <div className="flex">
      <div className="grow" />
      {value}/{limit}
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
  required: boolean;
}) {
  return (
    <label htmlFor={htmlFor}>
      {text}
      <Required required={required} />
    </label>
  );
}

function Required({ required }: { required: boolean }) {
  if (required) {
    return <span className="text-brand">*</span>;
  }

  return null;
}
