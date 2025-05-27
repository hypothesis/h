/**
 * Watch for changes in the size (`clientWidth` and `clientHeight`) of
 * an element.
 *
 * Returns a cleanup function which should be called to remove observers when
 * updates are no longer needed.
 *
 * @param element - HTML element to watch
 * @param onSizeChanged - Callback to invoke with the `clientWidth` and
 *   `clientHeight` of the element when a change in its size is detected.
 */
export function observeElementSize(
  element: Element,
  onSizeChanged: (width: number, height: number) => void,
): () => void {
  const observer = new ResizeObserver(() =>
    onSizeChanged(element.clientWidth, element.clientHeight),
  );
  observer.observe(element);
  return () => observer.disconnect();
}
