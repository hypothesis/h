/**
 * Test seam for updating {@link location.href}.
 */
// istanbul ignore next
export function setLocation(newLocation: string): void {
  window.location.href = newLocation;
}
