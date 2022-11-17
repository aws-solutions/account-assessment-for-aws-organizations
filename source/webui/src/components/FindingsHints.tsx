// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {HelpPanel, Icon} from "@cloudscape-design/components";

export function FindingsHints() {
  return <HelpPanel
    footer={
      <div>
        <h3>
          Learn more <Icon name="external"/>
        </h3>
        <ul>
          <li>
            <a
              href="https://docs.aws.amazon.com/solutions/latest/account-assessment-for-aws-organizations/solution-overview.html">Link
              to documentation</a>
          </li>
        </ul>
      </div>
    }
    header={<h2>Important Notes</h2>}>
    When migrating accounts between AWS Organizations, please keep in mind:
    <ul>
      <li>Changes to policies are <b>at your own discretion</b>. Make sure every policy meets your security requirements
        and
        review the impact of a change carefully.
      </li>
      <li>Engage with AWS professionals to review Organizations dependencies before migrating.</li>
      <li>Review dependencies outside of the scope of this solution that can impact migration.</li>
      <li>This solution does <b>not</b> check validity nor correctness of your resource-based policies.</li>
    </ul>
  </HelpPanel>
}