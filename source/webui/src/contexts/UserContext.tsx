// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {createContext, ReactNode, useEffect, useState} from 'react';
import {AuthUser, fetchUserAttributes, getCurrentUser, signInWithRedirect, signOut} from 'aws-amplify/auth';
import {Hub} from 'aws-amplify/utils';

export const UserContext = createContext<{
  user: AuthUser | null,
  email: string | null,
  orgId: string | null,
  signOut: () => Promise<void>,
  signInWithRedirect: () => Promise<void>
}>({
  user: null,
  email: null,
  orgId: null,
  signOut: () => Promise.resolve(),
  signInWithRedirect: () => Promise.resolve()
});
export const UserContextProvider = (props: { orgId: string | null, children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [email, setEmail] = useState<string | null>(null);

  Hub.listen('auth', ({payload}) => {
    switch (payload.event) {
      case 'signedOut':
        setUser(null);
        break;
      case 'signInWithRedirect':
        checkUser();
        break;
      default:
        break;
    }
  })

  useEffect(() => {
    Hub.listen('auth', ({payload}) => {
      switch (payload.event) {
        case 'signInWithRedirect':
          checkUser();
          break
        case 'signedOut':
          setUser(null);
          break
      }
    })
    checkUser();
  }, []);

  const checkUser = async () => {
    try {
      const responseUser: AuthUser | null = await getCurrentUser();
      setUser({
        ...responseUser
      })
      try {
        const userAttributesOutput = await fetchUserAttributes();
        setEmail(userAttributesOutput.email ?? null)
      } catch (e) {
        console.log(e);
      }
    } catch (error) {
      console.error(error);
      setUser(null)
    }
  };

  return (
    <UserContext.Provider value={{
      user,
      email,
      orgId: props.orgId,
      signOut,
      signInWithRedirect
    }}>
      {props.children}
    </UserContext.Provider>
  )
}