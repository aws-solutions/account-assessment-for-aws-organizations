// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createContext, useState} from 'react';

export const NotificationContext = createContext(null as any);
export const NotificationContextProvider = (props: any) => {
  const [notifications, setNotifications] = useState([]);

  return (
    <>
        <NotificationContext.Provider value={{notifications, setNotifications}}>
          {props.children}
        </NotificationContext.Provider>
    </>
  )
}