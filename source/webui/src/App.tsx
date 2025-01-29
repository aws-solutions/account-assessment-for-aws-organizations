// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {useContext, useEffect} from 'react';
import {UserContext} from "./contexts/UserContext";
import AppLayout from "@cloudscape-design/components/app-layout";
import {ButtonDropdownProps, Flashbar, Spinner, TopNavigation} from "@cloudscape-design/components";
import {Navigation} from "./components/SideNavigation";
import {AccountAssessmentBreadcrumbs, MainContentRoutes} from "./MainContentRoutes";
import {NotificationContext} from "./contexts/NotificationContext";
import {BrowserRouter} from "react-router-dom";
import {FindingsHints} from "./components/FindingsHints";

function App() {
  const {notifications} = useContext(NotificationContext);
  const {user, email, signInWithRedirect, signOut} = useContext(UserContext);

  useEffect(() => {
    if (!user)
      signInWithRedirect().catch((error) => {
        console.debug(error); // may throw UserAlreadyAuthenticatedException
      });
  })
  const [
    toolsOpen,
    setToolsOpen
  ] = React.useState<boolean>(true);

  const menuItemClick = async (props: CustomEvent<ButtonDropdownProps.ItemClickDetails>) => {
    const id = props.detail.id;
    if (id === 'signout') {
      signOut();
    }
  }

  if (!user)
    return <>
      <Spinner></Spinner>
      <div>Redirecting to login...</div>
    </>
  else return <>
    <div className="App">
      <TopNavigation identity={{} as any} i18nStrings={{} as any} utilities={[
        {
          type: "menu-dropdown",
          text: email ?? user.username,
          iconName: "user-profile",
          items: [
            {
              id: "documentation",
              text: "Documentation",
              href: "https://docs.aws.amazon.com/solutions/latest/account-assessment-for-aws-organizations/solution-overview.html",
              external: true,
              externalIconAriaLabel:
                " (opens in new tab)"
            },
            {
              id: "signout",
              text: "Sign out",
            }
          ],
          onItemClick: menuItemClick,
        }
      ]}/>
      <BrowserRouter>
        <AppLayout
          notifications={<Flashbar items={notifications}/>}
          navigation={<Navigation/>}
          content={<MainContentRoutes/>}
          breadcrumbs={<AccountAssessmentBreadcrumbs/>}
          tools={(<FindingsHints></FindingsHints>)}
          toolsOpen={toolsOpen}
          onToolsChange={event => setToolsOpen(event.detail.open)}
        />
      </BrowserRouter>;
    </div>
  </>;

}

export default App;
