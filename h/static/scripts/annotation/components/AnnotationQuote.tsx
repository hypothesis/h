import classnames from 'classnames';

import Excerpt from './Excerpt';
import StyledText from './StyledText';

type AnnotationQuoteProps = {
  quote: string;
  isHovered?: boolean;
  isOrphan?: boolean;
};

/**
 * Display the selected text from the document associated with an annotation.
 */
export default function AnnotationQuote({
  quote,
  isHovered,
  isOrphan,
}: AnnotationQuoteProps) {
  return (
    <Excerpt collapsedHeight={35} inlineControls={true} overflowThreshold={20}>
      <StyledText classes={classnames({ 'p-redacted-text': isOrphan })}>
        <blockquote
          className={classnames('hover:border-l-blue-quote', {
            'border-l-blue-quote': isHovered,
          })}
        >
          {quote}
        </blockquote>
      </StyledText>
    </Excerpt>
  );
}
