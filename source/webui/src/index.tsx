// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import "@cloudscape-design/global-styles/index.css"
import App from './App';
import {UserContextProvider} from "./contexts/UserContext";
import {NotificationContextProvider} from "./contexts/NotificationContext";
import {Provider} from "react-redux";
import {setupStore} from "./store/store.ts";
import {Amplify} from "aws-amplify";
import {ResourcesConfig} from "@aws-amplify/core";

loadConfigAndRenderApp();

export async function loadConfigAndRenderApp() {

  const response = await fetch('/aws-exports-generated.json', {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    }
  )
  const amplifyV1Config = await response.json();
  const orgId = amplifyV1Config.OrgId ?? null;

  // map legacy config to expected config format of Amplify gen2
  const amplifyV2Config: ResourcesConfig = {
    Auth: {
      Cognito: {
        userPoolId: amplifyV1Config.Auth.userPoolId,
        userPoolClientId: amplifyV1Config.Auth.userPoolWebClientId,
        loginWith: {
          oauth: {
            domain: amplifyV1Config.Auth.oauth.domain,
            redirectSignIn: [amplifyV1Config.Auth.oauth.redirectSignIn],
            redirectSignOut: [amplifyV1Config.Auth.oauth.redirectSignOut],
            responseType: "code",
            scopes: amplifyV1Config.Auth.oauth.scope,
            providers: []
          }
        }
      }
    },
    API: {
      REST: {
        AccountAssessmentApi: {
          endpoint: amplifyV1Config.API.endpoints[0].endpoint
        }
      }
    }
  };

  Amplify.configure(amplifyV2Config);
  const store = setupStore();

  const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
  );

  // React.StrictMode will call useEffect() twice during developments to help identify side effects.
  // this may lead to 2 identical http calls on page load. will not happen in production.
  const app =
    <React.StrictMode>
      <Provider store={store}>
        <UserContextProvider orgId={orgId}>
          <NotificationContextProvider>
            <App/>
          </NotificationContextProvider>
        </UserContextProvider>
      </Provider>
    </React.StrictMode>;

  root.render(
    app
  );
}

