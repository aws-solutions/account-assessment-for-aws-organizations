// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {render} from "@testing-library/react";
import {MemoryRouter} from "react-router-dom";
import {NotificationContext, NotificationContextProvider} from "../contexts/NotificationContext.tsx";
import {MainContentRoutes} from "../MainContentRoutes.tsx";
import {UserContext} from "../contexts/UserContext.tsx";
import {AuthUser} from "aws-amplify/auth";
import {Provider} from "react-redux";
import {setupStore} from "../store/store.ts";
import {Flashbar} from "@cloudscape-design/components";
import React, {useContext} from "react";

/*
 * Render a page within the context of a Router, redux store and NotificationContext.
 *
 * This function provides setup for component tests that
 * - interact with the store state,
 *  -navigate between pages
 *  and/or
 * - emit notifications.
 */
export function renderAppContent(props?: {
  initialRoute: string;
}) {
  const store = setupStore();

  const renderResult = render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[props?.initialRoute ?? '/']}>
        <UserContext.Provider value={{
          orgId: '',
          user: {} as AuthUser,
          email: '',
          signOut: () => Promise.resolve(),
          signInWithRedirect: () => Promise.resolve(),
        }}>
          <NotificationContextProvider>
            <AppWithNotifications></AppWithNotifications>
          </NotificationContextProvider>
        </UserContext.Provider>
      </MemoryRouter>
    </Provider>,
  );
  return {
    renderResult,
  };
}

const AppWithNotifications = () => {
  const {notifications} = useContext(NotificationContext);
  return <>
    <div data-testid={'flashbar'}>
      {notifications.length // render conditionally to avoid verbose warnings in tests that don't use the Flashbar
        ? <Flashbar items={notifications}/>
        : <></>}
    </div>
    <MainContentRoutes/>
  </>
}
