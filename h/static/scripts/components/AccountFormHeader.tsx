import { routes } from '../routes';
import TabLinks from './TabLinks';

/** Navigation tabs for the account forms. */
export default function AccountFormHeader() {
  return (
    <div className="mt-2 mb-6 border-b border-b-text-grey-6 py-2 flex flex-row items-center">
      <TabLinks>
        <TabLinks.Link
          testId="settings-link"
          href={routes.accountSettings}
          server
        >
          Account
        </TabLinks.Link>
        <TabLinks.Link testId="profile-link" href={routes.profile} server>
          Profile
        </TabLinks.Link>
        <TabLinks.Link
          testId="notifications-link"
          href={routes.accountNotifications}
          server
        >
          Notifications
        </TabLinks.Link>
        <TabLinks.Link
          testId="developer-link"
          href={routes.accountDeveloper}
          server
        >
          Developer
        </TabLinks.Link>
      </TabLinks>
    </div>
  );
}
