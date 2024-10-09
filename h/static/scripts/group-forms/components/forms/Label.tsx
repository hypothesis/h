import Star from './Star';

/**
 * A label for a form field.
 *
 * This includes an indicator for whether the field is required or not.
 */
export default function Label({
  id,
  htmlFor,
  text,
  required,
}: {
  id?: string;
  htmlFor?: string;
  text: string;
  required?: boolean;
}) {
  return (
    <label className="font-bold" id={id} htmlFor={htmlFor}>
      {text}
      {required && <Star />}
    </label>
  );
}
