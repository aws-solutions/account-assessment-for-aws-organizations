// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {BreadcrumbGroup} from '@cloudscape-design/components';
import {useLocation, useNavigate} from 'react-router-dom';
import {createBreadcrumbs} from './create-breadcrumbs.ts';

// Generates a BreadcrumbGroup based on the sections of the current path.
// This assumes that every path section is a page you can navigate to.
// If that is not the case for a certain path, provide custom Breadcrumbs in MainContentRoutes.ts
export const DefaultBreadcrumbs = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname;

  const breadCrumbItems = createBreadcrumbs(path);

  return (
    <BreadcrumbGroup
      onFollow={function (e: CustomEvent) {
        e.preventDefault(); // prevent page reload, use client side routing instead
        navigate(e.detail.href);
      }}
      items={breadCrumbItems}
    />
  );
};
