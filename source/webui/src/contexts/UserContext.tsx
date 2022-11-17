// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {createContext, useEffect, useState} from 'react';
import {Auth} from '@aws-amplify/auth';
import {Hub, HubCapsule} from '@aws-amplify/core';
import {CognitoUser} from "amazon-cognito-identity-js";


export const UserContext = createContext<CognitoUser | null>(null);
export const UserContextProvider = (props: any) => {
  const [user, setUser] = useState<CognitoUser | null>(null);
  const [progressCircle, setProgressCircle] = useState(true);

  Hub.listen('auth', (hubCapsule: HubCapsule) => {
    switch (hubCapsule.payload.event) {
      case 'signOut':
        setUser(null);
        break;
      case 'cognitoHostedUI':
        checkUser();
        break;
      default:
        break;
    }
  })

  useEffect(() => {
    Hub.listen('auth', (hubCapsule: HubCapsule) => {
      switch (hubCapsule.payload.event) {
        case 'cognitoHostedUI':
          checkUser();
          break
        case 'signOut':
          setUser(null);
          break
      }
    })
    checkUser();
  }, []);

  const checkUser = async () => {
    try {
      const responseUser: CognitoUser | null = await Auth.currentAuthenticatedUser()
      setUser(responseUser)
      setProgressCircle(false)
    } catch (error) {
      setUser(null)
      setProgressCircle(false)
    }
  };

  return (
    <>
      {progressCircle ? (
        'Loading'
      ) : (
          <UserContext.Provider value={user}>
            {props.children}
          </UserContext.Provider>
      )}
    </>
  )
}