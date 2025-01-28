// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import {PolicyModel} from "./PolicyExplorerModel"
import {Box, Button, CollectionPreferencesProps, Modal, SpaceBetween, TableProps} from "@cloudscape-design/components";

export const apiPathPolicyExplorer = '/policy-explorer';

interface PolicyModalProps {
  policy: string
}

const PolicyModal = (props: PolicyModalProps) => {
  const [visible, setVisible] = React.useState(false);

  return (
    <>
      {visible ? <Modal
        onDismiss={() => setVisible(false)}
        visible={visible}
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="primary" onClick={() => {
                setVisible(false)
              }}>Close</Button>
            </SpaceBetween>
          </Box>
        }
        header="Policy"
      >
        <pre>{JSON.stringify(JSON.parse(props.policy), undefined, 4)}</pre>
      </Modal> : <></>}
      <Button onClick={() => {
        setVisible(true)
      }}>View Policy</Button>
    </>
  )
}

export const policySearchColumns: Array<TableProps.ColumnDefinition<PolicyModel>> = [
  {
    header: "Policy Type",
    id: "PolicyType",
    cell: (item) => item.PartitionKey,
  },
  {
    header: "AccountId",
    id: "AccountId",
    cell: (item) => item.AccountId || '-',
    // width: 100
  },
  {
    header: "Region",
    id: "Region",
    cell: (item) => item.Region || '-',
    // width: 150
  },
  {
    header: "Service Name",
    id: "ServiceName",
    cell: (item) => item.Service || '-',
    // width: 200
  },
  {
    header: "Resource Name",
    id: "ResourceName",
    cell: (item) => item.ResourceIdentifier || '-',
    // width: 200
  },
  {
    header: "Resource",
    id: "Resource",
    cell: (item) => item.Resource || '-',
    // width: 200
  },
  {
    header: "Not Resource",
    id: "NotResourceName",
    cell: (item) => item.NotResource || '-',
    // width: 200
  },
  {
    header: "Action",
    id: "ActionName",
    cell: (item) => item.Action || '-',
    // width: 200
  },
  {
    header: "Not Action",
    id: "NotActionName",
    cell: (item) => item.NotAction || '-',
    // width: 200
  },
  {
    header: "Effect",
    id: "Effect",
    cell: (item) => item.Effect || '-',
    width: 200
  },
  {
    header: "Policy",
    id: "Policy",
    cell: (item) => <PolicyModal policy={item.Policy || '-'}></PolicyModal>,
    width: 200
  }
]
export const contentDisplayItems: Array<CollectionPreferencesProps.ContentDisplayItem> = [
  {
    id: "PolicyType",
    visible: false,
  },
  {
    id: "AccountId",
    visible: true,
  },
  {
    id: "Region",
    visible: false
  },
  {
    id: "ServiceName",
    visible: false
  },
  {
    id: "ResourceName",
    visible: true
  },
  {
    id: "Resource",
    visible: true
  },
  {
    id: "NotResourceName",
    visible: false
  },
  {
    id: "ActionName",
    visible: true
  },
  {
    id: "NotActionName",
    visible: false
  },
  {
    id: "Effect",
    visible: true
  },
  {
    id: "Policy",
    visible: true
  }
]
export const contentDisplayOptions: Array<CollectionPreferencesProps.ContentDisplayOption> = [
  {
    id: "PolicyType",
    alwaysVisible: false,
    label: "PolicyType"
  },
  {
    id: "AccountId",
    alwaysVisible: true,
    label: "AccountId"
  },
  {
    id: "Region",
    alwaysVisible: false,
    label: "Region"
  },
  {
    id: "ServiceName",
    alwaysVisible: false,
    label: "ServiceName"
  },
  {
    id: "ResourceName",
    alwaysVisible: true,
    label: "ResourceName"
  },
  {
    id: "Resource",
    alwaysVisible: true,
    label: "Resource"
  },
  {
    id: "NotResourceName",
    alwaysVisible: false,
    label: "NotResourceName"
  },
  {
    id: "ActionName",
    alwaysVisible: true,
    label: "ActionName"
  },
  {
    id: "NotActionName",
    alwaysVisible: false,
    label: "NotActionName"
  },
  {
    id: "Effect",
    alwaysVisible: true,
    label: "Effect"
  },
  {
    id: "Policy",
    alwaysVisible: true,
    label: "Policy"
  }
];

export const policyCsvHeader = "Account Id, Action, Effect, NotAction, NotResource, Policy Type, Region, Resource, Resource Identifier, Service";
export const policyCsvAttributes = ['AccountId', 'Action', 'Effect', 'NotAction', 'NotResource', 'PartitionKey', 'Region', 'Resource', 'ResourceIdentifier', 'Service'];