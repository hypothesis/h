import Star from './Star';

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
