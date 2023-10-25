// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createContext, useState, useMemo} from 'react';

export const NotificationContext = createContext(null as any);


export const NotificationContextProvider = (props: any) => {
  const [notifications, setNotifications] = useState([]);

  const notificationValue = useMemo(() => ({notifications, setNotifications}), [notifications, setNotifications])

  return (
    <>
        <NotificationContext.Provider value={notificationValue}>
          {props.children}
        </NotificationContext.Provider>
    </>
  )
}