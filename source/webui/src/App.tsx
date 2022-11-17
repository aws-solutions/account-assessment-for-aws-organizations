// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {useContext, useEffect} from 'react';
import './App.css';
import {Auth} from "@aws-amplify/auth";
import {UserContext} from "./contexts/UserContext";
import AppLayout from "@cloudscape-design/components/app-layout";
import {ButtonDropdownProps, Flashbar, Spinner, TopNavigation} from "@cloudscape-design/components";
import {Navigation} from "./components/SideNavigation";
import {breadcrumbs, mainContentRoutes} from "./MainContentRoutes";
import {NotificationContext} from "./contexts/NotificationContext";
import {BrowserRouter} from "react-router-dom";
import {FindingsHints} from "./components/FindingsHints";

function App() {
  const {notifications} = useContext(NotificationContext);
  const user = useContext(UserContext);

  useEffect(() => {
    if (!user)
      Auth.federatedSignIn().catch((error) => {
        console.error(error);
      });
  })
  const [
    toolsOpen,
    setToolsOpen
  ] = React.useState<boolean>(true);

  const menuItemClick = async (props: CustomEvent<ButtonDropdownProps.ItemClickDetails>) => {
    const id = props.detail.id;
    if (id === 'signout') {
      Auth.signOut().catch((error: Error) => {
        console.error("Error occurred while signing out.", error);
      });
    }
  }

  if (!user)
    return <>
      <Spinner></Spinner>
      <div>Redirecting to login...</div>
    </>
  else {
    return <>
      <div className="App">
        <TopNavigation identity={{} as any} i18nStrings={{} as any} utilities={[
          {
            type: "menu-dropdown",
            text: (user as any)?.attributes?.email,
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
            content={mainContentRoutes}
            breadcrumbs={breadcrumbs}
            tools={(<FindingsHints></FindingsHints>)}
            toolsOpen={toolsOpen}
            onToolsChange={event => setToolsOpen(event.detail.open)}
          />
        </BrowserRouter>;
      </div>
    </>;
  }
}

export default App;
