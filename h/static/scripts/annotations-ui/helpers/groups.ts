export type GroupType = 'private' | 'restricted' | 'open';

export type Group = {
  type: GroupType;
  links: {
    html?: string;
  };
  name: string;
};
