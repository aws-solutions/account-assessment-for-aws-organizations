// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {ReactNode} from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import "@cloudscape-design/global-styles/index.css"
import App from './App';
import {UserContextProvider} from "./contexts/UserContext";
import {NotificationContextProvider} from "./contexts/NotificationContext";
import {Auth} from "@aws-amplify/auth";
import Amplify from "@aws-amplify/core";

const app =
    <React.StrictMode>
      <UserContextProvider>
        <NotificationContextProvider>
          <App/>
        </NotificationContextProvider>
      </UserContextProvider>
    </React.StrictMode>;

loadConfigAndRenderApp(app);

type EndpointConfig = {
  name: string,
  endpoint: string,
  custom_header: () => {}
}

export async function loadConfigAndRenderApp(app: ReactNode) {
  const response = await fetch('/aws-exports-generated.json', {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
  )

  const awsconfig = await response.json();

  const customHeaderBuilder: () => Promise<{ Authorization: string }> = async () => {
    const session = await Auth.currentSession();
    return {Authorization: `Bearer ${session.getIdToken().getJwtToken()}`}
  }
  for (const it of awsconfig.API.endpoints) {
    (it as EndpointConfig).custom_header = customHeaderBuilder;
  }

  Amplify.Logger.LOG_LEVEL = awsconfig.loggingLevel || 'ERROR';
  Amplify.configure(awsconfig);

  const root = ReactDOM.createRoot(
      document.getElementById('root') as HTMLElement
  );
  root.render(
      app
  );
}

