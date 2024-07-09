import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

export default function CreateGroupForm() {
  return (
    <>
      <h1 className="mt-[55px] mb-[30px] text-[#3f3f3f] text-[19px] leading-[15px]">
        Create a new private group
      </h1>

      <form>
        <div className="mb-[15px]">
          <label
            htmlFor="name"
            className="text-[#7a7a7a] text-[13px] leading-[15px]"
          >
            Name<span className="text-[#d00032]">*</span>
          </label>
          <Input id="name" autofocus autocomplete="off" required />
          <div className="flex">
            <div className="grow" />
            <span className="text-[#7a7a7a] text-[13px] leading-[15px]">
              0/25
            </span>
          </div>
        </div>

        <div className="mb-[15px]">
          <label
            htmlFor="description"
            className="text-[#7a7a7a] text-[13px] leading-[15px]"
          >
            Description
          </label>
          <Textarea id="description" />
          <div className="flex">
            <div className="grow" />
            <span className="text-[#7a7a7a] text-[13px] leading-[15px]">
              0/250
            </span>
          </div>
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
