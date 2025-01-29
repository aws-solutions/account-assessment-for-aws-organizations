// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Route, Routes, useNavigate} from "react-router-dom";
import {DelegatedAdminPage} from "./components/delegated-admin/DelegatedAdminPage";
import {TrustedAccessPage} from "./components/trusted-access/TrustedAccessPage";
import {JobHistoryPage} from "./components/jobs/JobHistoryPage";
import {JobPage} from "./components/jobs/JobPage";
import {ResourceBasedPoliciesPage} from "./components/resource-based-policies/ResourceBasedPoliciesPage";
import {BreadcrumbGroup, Container, ContentLayout, Header} from "@cloudscape-design/components";
import {LandingPage} from "./components/landing-page/LandingPage";
import {PolicyExplorerPage} from "./components/policy-explorer/PolicyExplorerPage";
import React from "react";
import {DefaultBreadcrumbs} from "./components/navigation/DefaultBreadcrumbs.tsx";

export const MainContentRoutes = () =>
  <Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/jobs" element={<JobHistoryPage/>}/>
    <Route path="/jobs/:assessmentType/:id" element={<JobPage/>}/>
    <Route path="/delegated-admin"
           element={<DelegatedAdminPage/>}/>
    <Route path="/trusted-access" element={<TrustedAccessPage/>}/>
    <Route path="/resource-based-policy"
           element={<ResourceBasedPoliciesPage/>}/>
    <Route path="/policy-explorer" element={<PolicyExplorerPage/>}/>
    <Route
      path="*"
      element={
        <ContentLayout header={<Header>Error</Header>}>
          <Container header={<Header>Page not found 😿</Header>}></Container>
        </ContentLayout>
      }
    />
  </Routes>

export const AccountAssessmentBreadcrumbs = () => {
  const navigate = useNavigate();
  return <Routes>
    <Route path="/jobs/:assessmentType/:id" element={<BreadcrumbGroup
      onFollow={function (e: CustomEvent) {
        e.preventDefault(); // prevent page reload, use client side routing instead
        navigate(e.detail.href);
      }}
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/jobs",
          text: "Job History"
        },
        {
          href: "",
          text: "Job Details"
        }
      ]}
    />}/>
    <Route path="*" element={<DefaultBreadcrumbs/>}/>
  </Routes>;
};