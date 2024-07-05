import { Button, Input, Textarea } from '@hypothesis/frontend-shared';

export default function CreateGroupForm() {
  return (
    <>
      <h1>Create a new private group</h1>

      <form>
        <div>
          <label for="name">Name*</label>
          <Input id="name" autofocus autocomplete="off" required />
          0/25
        </div>

        <div>
          <label for="description">Description</label>
          <Textarea id="description" />
          0/250
        </div>

        <div>
          <Button variant="primary">Create group</Button>
        </div>
      </form>

      <footer>*Required</footer>
    </>
  );
}
