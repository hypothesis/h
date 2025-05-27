import { Button, CollapseIcon, ExpandIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useContext, useState } from 'preact/hooks';

import { Config } from '../../group-forms/config';
import type { APIAnnotationData } from '../../group-forms/utils/api';
import Excerpt from './Excerpt';
import MarkdownView from './MarkdownView';
import TagList from './TagList';
import TagListItem from './TagListItem';

type ToggleExcerptButtonProps = {
  classes?: string;
  setCollapsed: (collapse: boolean) => void;
  collapsed: boolean;
};

/**
 * Button to expand or collapse the annotation excerpt (content)
 */
function ToggleExcerptButton({
  classes,
  setCollapsed,
  collapsed,
}: ToggleExcerptButtonProps) {
  const toggleText = collapsed ? 'More' : 'Less';
  return (
    <Button
      classes={classnames('text-grey-7 font-normal', classes)}
      expanded={!collapsed}
      onClick={() => setCollapsed(!collapsed)}
      title={`Toggle visibility of full annotation text: Show ${toggleText}`}
    >
      <div className="flex items-center gap-x-2">
        {collapsed ? (
          <ExpandIcon className="w-3 h-3" />
        ) : (
          <CollapseIcon className="w-3 h-3" />
        )}
        <div>{toggleText}</div>
      </div>
    </Button>
  );
}

export type AnnotationBodyProps = {
  annotation: APIAnnotationData;
};

/**
 * Display the rendered content of an annotation.
 */
export default function AnnotationBody({ annotation }: AnnotationBodyProps) {
  // Should the text content of `Excerpt` be rendered in a collapsed state,
  // assuming it is collapsible (exceeds allotted collapsed space)?
  const [collapsed, setCollapsed] = useState(true);

  // Does the text content of `Excerpt` take up enough vertical space that
  // collapsing/expanding is relevant?
  const [collapsible, setCollapsible] = useState(false);

  const config = useContext(Config)!;
  const mentionsEnabled = config.features.at_mentions;

  // If there is a draft use the tag and text from it.
  const tags = annotation.tags;
  const text = annotation.text;
  const showExcerpt = text.length > 0;
  const showTagList = tags.length > 0;

  return (
    <div className="space-y-4">
      {showExcerpt && (
        <Excerpt
          collapse={collapsed}
          collapsedHeight={400}
          inlineControls={false}
          onCollapsibleChanged={setCollapsible}
          onToggleCollapsed={setCollapsed}
          overflowThreshold={20}
        >
          <MarkdownView
            markdown={text}
            mentions={annotation.mentions}
            mentionsEnabled={mentionsEnabled}
            mentionMode="username"
          />
        </Excerpt>
      )}
      {(collapsible || showTagList) && (
        <div className="flex flex-row gap-x-2">
          <div className="grow">
            {showTagList && (
              <TagList>
                {tags.map(tag => {
                  return <TagListItem key={tag} tag={tag} href={'TODO'} />;
                })}
              </TagList>
            )}
          </div>
          {collapsible && (
            <div>
              <ToggleExcerptButton
                classes={classnames(
                  // Pull button up toward bottom of excerpt content
                  '-mt-3',
                )}
                collapsed={collapsed}
                setCollapsed={setCollapsed}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
