import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

export default function CreateGroupForm() {
  return (
    <>
      <h1 class="mt-[55px] mb-[30px] text-[#3f3f3f] text-[19px] leading-[15px]">
        Create a new private group
      </h1>

      <form>
        <div class="mb-[15px]">
          <label for="name" class="text-[#7a7a7a] text-[13px] leading-[15px]">
            Name<span class="text-[#d00032]">*</span>
          </label>
          <Input id="name" autofocus autocomplete="off" required />
          <div class="flex">
            <div class="grow"></div>
            <span class="text-[#7a7a7a] text-[13px] leading-[15px]">0/25</span>
          </div>
        </div>

        <div class="mb-[15px]">
          <label
            for="description"
            class="text-[#7a7a7a] text-[13px] leading-[15px]"
          >
            Description
          </label>
          <Textarea id="description" />
          <div class="flex">
            <div class="grow"></div>
            <span class="text-[#7a7a7a] text-[13px] leading-[15px]">0/250</span>
          </div>
        </div>

        <div class="flex">
          <div class="grow"></div>
          <div>
            <Button variant="primary">Create group</Button>
          </div>
        </div>
      </form>

      <footer class="text-[#7a7a7a] text-[13px] leading-[15px] mt-[50px] pt-[15px] border-t border-t-[#dbdbdb]">
        <div class="flex">
          <div class="grow"></div>
          <div>
            <span class="text-[#d00032]">*</span> Required
          </div>
        </div>
      </footer>
    </>
  );
}
