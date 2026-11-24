// jsdom does not implement modal dialog methods.
export function stubDialog(): void {
  const prototype = HTMLDialogElement.prototype;

  if (prototype.showModal == null) {
    prototype.showModal = function showModal () {
      this.open = true;
    };
  }
  if (prototype.close == null) {
    prototype.close = function close () {
      this.open = false;
    };
  }
}
