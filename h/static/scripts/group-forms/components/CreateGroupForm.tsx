import { useId } from 'preact/hooks';

import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

export default function CreateGroupForm() {
  const nameId = useId();
  const descriptionId = useId();

  return (
    <>
      <h1 className="mt-[55px] mb-[30px] text-[#3f3f3f] text-[19px] leading-[15px]">
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
          <div>
            <Button variant="primary">Create group</Button>
          </div>
        </div>
      </form>

      <footer className="text-[#7a7a7a] text-[13px] leading-[15px] mt-[50px] pt-[15px] border-t border-t-[#dbdbdb]">
        <div className="flex">
          <div className="grow" />
          <div>
            <span className="text-[#d00032]">*</span> Required
          </div>
        </div>
      </footer>
    </>
  );
}

function CharacterCounter({ value, limit }: { value: number; limit: number }) {
  return (
    <div className="flex">
      <div className="grow" />
      <span className="text-[#7a7a7a] text-[13px] leading-[15px]">
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
  required: boolean;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="text-[#7a7a7a] text-[13px] leading-[15px]"
    >
      {text}
      <Required required={required} />
    </label>
  );
}

function Required({ required }: { required: boolean }) {
  if (required) {
    return <span className="text-[#d00032]">*</span>;
  }

  return null;
}
