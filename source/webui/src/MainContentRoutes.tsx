// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {Route, Routes} from "react-router-dom";
import {DelegatedAdminPage} from "./components/delegated-admin/DelegatedAdminPage";
import {TrustedAccessPage} from "./components/trusted-access/TrustedAccessPage";
import React from "react";
import {JobHistoryPage} from "./components/jobs/JobHistoryPage";
import {JobPage} from "./components/jobs/JobPage";
import {ResourceBasedPoliciesPage} from "./components/resource-based-policies/ResourceBasedPoliciesPage";
import {BreadcrumbGroup} from "@cloudscape-design/components";
import {ConfigureScanPage} from "./components/resource-based-policies/ConfigureScanPage";
import {LandingPage} from "./components/landing-page/LandingPage";

export const mainContentRoutes =
  <Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/jobs" element={<JobHistoryPage/>}/>
    <Route path="/jobs/:assessmentType/:id" element={<JobPage/>}/>
    <Route path="/assessments/delegated-admin"
           element={<DelegatedAdminPage/>}/>
    <Route path="/assessments/trusted-access" element={<TrustedAccessPage/>}/>
    <Route path="/assessments/resource-based-policy"
           element={<ResourceBasedPoliciesPage/>}/>
    <Route path="/assessments/resource-based-policy/configure-scan"
           element={<ConfigureScanPage/>}/>
  </Routes>

export const breadcrumbs =
  <Routes>
    <Route path="/" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        }
      ]}
    />}/>
    <Route path="/jobs" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/jobs",
          text: "Job History"
        }
      ]}
    />}/>
    <Route path="/jobs/:assessmentType/:id" element={<BreadcrumbGroup
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
    <Route path="/assessments/delegated-admin" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/assessments/delegated-admin",
          text: "Delegated Admin Accounts"
        }
      ]}
    />}/>
    <Route path="/assessments/trusted-access" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/assessments/trusted-access",
          text: "Trusted Access"
        }
      ]}
    />}/>
    <Route path="/assessments/resource-based-policy" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/assessments/resource-based-policy",
          text: "Resource-Based Policies"
        }
      ]}
    />}/>
    <Route path="/assessments/resource-based-policy/configure-scan" element={<BreadcrumbGroup
      items={[
        {
          href: "/",
          text: "Home"
        },
        {
          href: "/assessments/resource-based-policy",
          text: "Resource-Based Policies"
        },
        {
          href: "/assessments/resource-based-policy/configure-scan",
          text: "Configure Scan"
        }
      ]}
    />}/>
  </Routes>;