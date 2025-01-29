// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Button,
  Container,
  Form,
  FormField,
  Grid,
  Header,
  Input,
  SpaceBetween,
  Tiles,
  Toggle,
} from "@cloudscape-design/components";
import {useContext, useState} from "react";
import {FiltersForPolicySearch, PolicySearchModel, PolicyTypes} from "./PolicyExplorerModel";
import {useDispatch} from "react-redux";
import {fetchPolicyModels} from "../../store/policy-model-thunks.ts";
import {UserContext} from "../../contexts/UserContext.tsx";
import {useLocation} from "react-router-dom";

type Effect = 'Allow' | 'Deny';

export const SearchForm = ({resetTableState}: { resetTableState: () => void }) => {
  const dispatch = useDispatch<any>();
  const {orgId} = useContext(UserContext);
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const policyType = queryParams.get('policyType') as PolicyTypes | null;

  const [policyTypeSelected, setPolicyTypeSelected] = useState(policyType ?? PolicyTypes.IDENTITY_BASED_POLICIES);
  const [extraFiltersExpanded, setExtraFiltersExpanded] = useState<boolean>(false);
  const [filters, setFilters] = useState<FiltersForPolicySearch>({
    region: 'GLOBAL',
    condition: policyType === PolicyTypes.RESOURCE_BASED_POLICIES && orgId ? orgId : ''
  });


  function clearSearchFields() {
    setPolicyTypeSelected(PolicyTypes.IDENTITY_BASED_POLICIES);
    setFilters({region: 'GLOBAL'});
  }

  const searchParams: PolicySearchModel = {
    policyType: policyTypeSelected,
    filters
  };

  const startSearch = () => {
    dispatch(fetchPolicyModels(searchParams));
    resetTableState();
  };

  function addOrgIdToCondition() {
    setFilters({condition: `${filters.condition ?? ''}${orgId ?? ''}`});
  }

  return (
    <Form data-testid={'search-form'}>
      <SpaceBetween size="l">
        <Container data-testid={'policy-type'}>
          <FormField label="Select Policy Type" stretch={true}>
            <Tiles
              items={[
                {
                  value: PolicyTypes.IDENTITY_BASED_POLICIES,
                  label: "Identity Based Policies",
                  description:
                    "Policies defined in IAM and inline policies for each IAM Role.",
                },
                {
                  value: PolicyTypes.RESOURCE_BASED_POLICIES,
                  label: "Resource Based Policies",
                  description:
                    "Resource Based Policies - policies defined for resources such as KMS, Lex.",
                },
                {
                  value: PolicyTypes.SERVICE_CONTROL_POLICIES,
                  label: "Service Control Policies",
                  description:
                    "Service Control Policies - policies defined for management account for the organizations.",
                },
              ]}
              value={policyTypeSelected}
              onChange={(e) => {
                clearSearchFields();
                setPolicyTypeSelected(
                  e.detail.value === PolicyTypes.IDENTITY_BASED_POLICIES ? PolicyTypes.IDENTITY_BASED_POLICIES :
                    e.detail.value === PolicyTypes.RESOURCE_BASED_POLICIES ? PolicyTypes.RESOURCE_BASED_POLICIES :
                      e.detail.value === PolicyTypes.SERVICE_CONTROL_POLICIES ? PolicyTypes.SERVICE_CONTROL_POLICIES :
                        PolicyTypes.IDENTITY_BASED_POLICIES)
              }}
            />
          </FormField>
        </Container>
        <Container data-testid={'search-criteria'}
                   header={<Header variant="h2" actions={
                     <SpaceBetween size={"s"} direction={"horizontal"}>
                       <Toggle
                         onChange={({detail}) =>
                           setExtraFiltersExpanded(detail.checked)
                         }
                         checked={extraFiltersExpanded}
                       >
                         Search for advanced policy elements
                       </Toggle>
                     </SpaceBetween>
                   }>Search criteria</Header>}
                   footer={
                     <SpaceBetween direction="horizontal" size="xs">
                       {orgId ? <Button onClick={addOrgIdToCondition}
                                        disabled={filters.condition?.includes(orgId)}
                       >
                         Add OrgId
                       </Button> : <></>}
                       <Button onClick={clearSearchFields}>
                         Clear Fields
                       </Button>
                       <Button data-testid="search" variant="primary" onClick={startSearch}>
                         Search
                       </Button>
                     </SpaceBetween>
                   }
        >

          {policyTypeSelected === PolicyTypes.RESOURCE_BASED_POLICIES ?
            <FormField label="Region" stretch={true}>
              <Input
                value={filters.region ?? ''}
                onChange={(event) => setFilters((prevFilters) => ({
                  ...prevFilters,
                  region: event.detail.value
                }))}
              />
            </FormField> : <></>
          }

          <Grid
            gridDefinition={[
              {colspan: {default: 12, xxs: 6}},
              {colspan: {default: 12, xxs: 6}},
            ]}
          >
            <SpaceBetween size={'l'} direction={"vertical"}>
              {policyTypeSelected === PolicyTypes.RESOURCE_BASED_POLICIES ?
                <FormField label="Principal">
                  <Input
                    value={filters.principal ?? ''}
                    onChange={(event) => setFilters((prevFilters) => ({
                      ...prevFilters,
                      principal: event.detail.value
                    }))}
                  />
                </FormField> : <></>
              }
              <FormField label="Action" stretch={true}>
                <Input
                  value={filters.action ?? ''}
                  onChange={(event) => setFilters((prevFilters) => ({
                    ...prevFilters,
                    action: event.detail.value
                  }))}
                />
              </FormField>
              <FormField label="Resource" stretch={true}>
                <Input
                  value={filters.resource ?? ''}
                  onChange={(event) => setFilters((prevFilters) => ({
                    ...prevFilters,
                    resource: event.detail.value
                  }))}
                />
              </FormField>
              <FormField label="Condition" stretch={true}>
                <Input
                  value={filters.condition ?? ''}
                  onChange={(event) => setFilters((prevFilters) => ({
                    ...prevFilters,
                    condition: event.detail.value
                  }))}
                />
              </FormField>
            </SpaceBetween>
            <SpaceBetween size={'l'} direction={"vertical"}>

              {extraFiltersExpanded ? <>
                {policyTypeSelected === PolicyTypes.RESOURCE_BASED_POLICIES ?
                  <FormField label="NotPrincipal">
                    <Input
                      value={filters.notPrincipal ?? ''}
                      onChange={(event) => setFilters((prevFilters) => ({
                        ...prevFilters,
                        notPrincipal: event.detail.value
                      }))}
                    />
                  </FormField>
                  : <></>}
                <FormField label="NotAction" stretch={true}>
                  <Input
                    value={filters.notAction ?? ''}
                    onChange={(event) => setFilters((prevFilters) => ({
                      ...prevFilters,
                      notAction: event.detail.value
                    }))}
                  />
                </FormField>
                <FormField label="NotResource" stretch={true}>
                  <Input
                    value={filters.notResource ?? ''}
                    onChange={(event) => setFilters((prevFilters) => ({
                      ...prevFilters,
                      notResource: event.detail.value
                    }))}
                  />
                </FormField>
              </> : <></>}

              <FormField label="Effect" stretch={true}>
                <SpaceBetween size="l">
                  <Tiles columns={1}
                         onChange={({detail}) => setFilters((prevFilters) => ({
                           ...prevFilters,
                           effect: ['Allow', 'Deny'].includes(detail.value) ? (detail.value as Effect) : undefined
                         }))}
                         value={filters.effect ?? ""}
                         items={[
                           {value: "", label: "Any"},
                           {value: "Allow", label: "Allow"},
                           {value: "Deny", label: "Deny"}
                         ]}
                         name="Effect"
                  />
                </SpaceBetween>
              </FormField>
            </SpaceBetween>
          </Grid>
        </Container>
      </SpaceBetween>
    </Form>
  );
};
