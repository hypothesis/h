export default function CreateGroupForm() {
  return (
    <>
      <h1>Create a new private group</h1>

      <form>
        <div>
          <label for="name">
            Name <span>*</span>
          </label>
          <input type="text" id="name" autofocus autocomplete="off" required />
          <span>0/25</span>
        </div>

        <div>
          <label for="description">Description</label>
          <textarea id="description"></textarea>
          <span>0/250</span>
        </div>

        <div>
          <div>
            <button>Create group</button>
          </div>
        </div>
      </form>

      <footer>
        <span>
          <span>*</span>
          <span>Required</span>
        </span>
      </footer>
    </>
  );
}
