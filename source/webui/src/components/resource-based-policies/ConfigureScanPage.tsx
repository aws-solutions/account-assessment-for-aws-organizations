// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Button,
  ContentLayout,
  Form,
  FormField,
  Input,
  Multiselect,
  RadioGroup,
  Select,
  SpaceBetween,
  Textarea
} from "@cloudscape-design/components";
import Header from "@cloudscape-design/components/header";
import * as React from "react";
import {useContext, useEffect, useState} from "react";
import Container from "@cloudscape-design/components/container";
import {useNavigate} from "react-router-dom";
import {get, post} from "../../util/ApiClient";
import {NotificationContext} from "../../contexts/NotificationContext";
import {JobModel} from "../jobs/JobModel";
import {apiPathResourceBasedPolicies} from "./ResourceBasedPoliciesDefinitions";
import {ConfigurationModel, RegionModel, ServiceModel} from "./ResourceBasedPolicyModel";
import {OptionDefinition} from "@cloudscape-design/components/internal/components/option/interfaces";

const AWS_ACCOUNT_ID_REGEX = /^\d{12}$/;
const AWS_ORG_UNIT_ID_REGEX = /^ou-[a-z0-9]{4,32}-[a-z0-9]{8,32}$/;
const CONFIG_NAME_REGEX = /^[a-zA-Z0-9_-]{1,64}$/;

const apiPathScanConfigurations = '/scan-configs';
type RegionOption = {
  label: string,
  value: string,
  description: string
}
type ServiceOption = {
  label: string,
  value: string,
}
type SupportedConfiguration = {
  SavedConfigurations: ConfigurationModel[]
  SupportedServices: ServiceModel[]
  SupportedRegions: RegionModel[]
}

export function compareOptions(option: { value: string }, otherOption: { value: string }) {
  if (option.value > otherOption.value) {
    return 1;
  } else if (option.value === otherOption.value) {
    return 0;
  } else {
    return -1;
  }
}

export const ConfigureScanPage = () => {

  const [newOrLoad, setNewOrLoad] = useState<string>('new');
  const [accountSelectionStrategy, setAccountSelectionStrategy] = useState<string>('all');
  const [accountIdsToScan, setAccountIdsToScan] = useState('');
  const [organizationalUnitIdsToScan, setOrganizationalUnitIdsToScan] = useState('');
  const [
    scanConfigurations,
    setScanConfigurations
  ] = React.useState<OptionDefinition[]>([]);
  const [
    supportedRegions,
    setSupportedRegions
  ] = React.useState<RegionOption[]>([]);
  const [
    supportedServices,
    setSupportedServices
  ] = React.useState<ServiceOption[]>([]);
  const [
    selectedConfig,
    setSelectedConfig
  ] = React.useState<OptionDefinition | null>(null);
  const [
    selectedRegions,
    setSelectedRegions
  ] = React.useState<RegionOption[]>([]);
  const [
    selectedServices,
    setSelectedServices
  ] = React.useState<ServiceOption[]>([]);
  const [
    configName,
    setConfigName
  ] = React.useState<string>('');
  const [configNameValidationError, setConfigNameValidationError] = useState('');
  const [startingScan, setStartingScan] = useState(false);
  const [accountIdValidationError, setAccountIdValidationError] = useState('');
  const [organizationalUnitIdValidationError, setOrganizationalUnitIdValidationError] = useState('');
  const {notifications, setNotifications} = useContext(NotificationContext);
  const navigate = useNavigate();

  function populateDropdowns(responseBody: SupportedConfiguration) {
    const {SavedConfigurations, SupportedServices, SupportedRegions} = responseBody;
    const scanConfigurationOptions = SavedConfigurations.map(it => {
      return {label: it.ConfigurationName, value: it.ConfigurationName, ...it}
    })
    setScanConfigurations(scanConfigurationOptions);

    const serviceOptions = SupportedServices.map(it => {
      return {label: it.FriendlyName, value: it.ServiceName, description: it.ServiceName}
    }).sort((r1, r2) => compareOptions(r1, r2))
    setSupportedServices(serviceOptions);

    const regionOptions = SupportedRegions.map(it => {
      return {label: it.RegionName, value: it.Region, description: it.Region}
    }).sort((r1, r2) => compareOptions(r1, r2))
    setSupportedRegions(regionOptions);
  }

  useEffect(() => {
    setNotifications([]);
    get<SupportedConfiguration>(apiPathScanConfigurations).then((response) => {

      if (response.responseBody) {
        populateDropdowns(response.responseBody);
      } else {
        setNotifications([...notifications, {
          header: 'Error',
          content: 'Failed to load scan configurations.',
          type: 'error',
          dismissible: true,
          onDismiss: () => setNotifications([])
        }]);
      }
    });
  }, []);

  const parseAccountIds = (accountIdsToScan: string) => {
    const commaSeparatedItems = accountIdsToScan.replace('\n', ',');
    const doubleCommasRemoved = commaSeparatedItems.replace(',,', ',');
    const rawAccountIds = doubleCommasRemoved.split(',');
    const trimmedAccountIds = rawAccountIds.map(it => it.trim());
    const validIds = trimmedAccountIds.filter(it => it); // filter out empty strings
    const invalidIds = validIds.filter(it => !it.match(AWS_ACCOUNT_ID_REGEX))
    if (invalidIds.length > 0)
      setAccountIdValidationError(`The following entries are not valid AWS account ids: ${invalidIds.join(', ')}`);
    else
      setAccountIdValidationError(``);

    return {validIds, invalidIds}
  }

  const parseOrganizationalUnitIds = (ouIdsToScan: string) => {
    const commaSeparatedItems = ouIdsToScan.replace('\n', ',');
    const doubleCommasRemoved = commaSeparatedItems.replace(',,', ',');
    const rawOuIds = doubleCommasRemoved.split(',');
    const trimmedOuIds = rawOuIds.map(it => it.trim());
    const validIds = trimmedOuIds.filter(it => it); // filter out empty strings
    const invalidIds = validIds.filter(it => !it.match(AWS_ORG_UNIT_ID_REGEX))
    if (invalidIds.length > 0)
      setOrganizationalUnitIdValidationError(`The following entries are not valid organizational unit ids: ${invalidIds.join(', ')}`);
    else
      setOrganizationalUnitIdValidationError(``);

    return {validIds, invalidIds}
  }

  const startFullScan = () => {
    startScan({}); // Each config property empty means 'scan all'
  };

  const validateConfigAndStartScan = () => {
    const configNameIsValid = validateConfigName(configName);
    let validationResult;
    if (accountSelectionStrategy === 'listed')
      validationResult = parseAccountIds(accountIdsToScan);
    else if (accountSelectionStrategy === 'org-units')
      validationResult = parseOrganizationalUnitIds(organizationalUnitIdsToScan);

    if (configNameIsValid && !validationResult?.invalidIds.length) {
      const config: ConfigurationModel = {
        Regions: selectedRegions.map(it => it.value),
        ServiceNames: selectedServices.map(it => it.value)
      };
      if (configName) config.ConfigurationName = configName;
      if (accountSelectionStrategy === 'listed') config.AccountIds = validationResult?.validIds;
      if (accountSelectionStrategy === 'org-units') config.OrgUnitIds = validationResult?.validIds;
      startScan(config);
    }
  };

  function startScan(config: ConfigurationModel) {
    setNotifications([]);
    setStartingScan(true);

    post<JobModel>(apiPathResourceBasedPolicies, {response: true, body: config}).then((state) => {
        if (state.error) {
          setNotifications([{
            header: state.error.Error,
            content: state.error.Message,
            type: 'error',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
          setStartingScan(false);
          return;
        }

        const job: JobModel | null = state.responseBody;
        if (job?.JobStatus === 'ACTIVE') {
          setNotifications([{
            header: 'Scan started',
            content: `Job with ID ${job.JobId} in progress.`,
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
          navigate(`/jobs/${job.AssessmentType}/${job.JobId}`);
        } else if (job?.JobStatus === 'FAILED') {
          setNotifications([{
            header: 'Scan failed',
            content: `Job with ID ${job.JobId} failed. For details please check the Cloudwatch Logs.`,
            type: 'error',
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
        } else {
          setNotifications([{
            header: 'Unexpected response',
            content: `Job responded in an unexpected way. For details please check the Cloudwatch Logs.`,
            dismissible: true,
            onDismiss: () => setNotifications([])
          }]);
        }
        setStartingScan(false);
      }
    );
  }

  function validateConfigName(value: string) {
    const isValid = !value || value.match(CONFIG_NAME_REGEX);
    if (isValid)
      setConfigNameValidationError('');
    else
      setConfigNameValidationError('Invalid configuration name');
    return isValid;
  }

  function populateForm(selectedConfig: OptionDefinition) {
    const config = selectedConfig as ConfigurationModel;
    if (config.AccountIds?.length) {
      setAccountIdsToScan(config.AccountIds.join(',\n'));
      setAccountSelectionStrategy('listed');
    } else if (config.OrgUnitIds?.length) {
      setOrganizationalUnitIdsToScan(config.OrgUnitIds.join(',\n'));
      setAccountSelectionStrategy('org-units');
    }
    if (config.Regions?.length) {
      const regionOptions: RegionOption[] = config.Regions.map(region => {
        return supportedRegions.find(it => it.value === region)!
      }).filter(it => !!it);
      setSelectedRegions(regionOptions);
    }
    if (config.ServiceNames?.length) {
      const serviceOptions: ServiceOption[] = config.ServiceNames.map(serviceName => {
        return supportedServices.find(it => {
          return it.value === serviceName;
        })!
      }).filter(it => !!it);
      setSelectedServices(serviceOptions);
    }
    setConfigName(config.ConfigurationName || '');
  }

  return <ContentLayout
    header={
      <Header variant="h1"
              description="Define the scope of the scan for resource-based policies."
              actions={
                <Button variant="primary" onClick={startFullScan}>Start Full Scan</Button>
              }>
        Configure Scan
      </Header>
    }
  >

    <SpaceBetween size="l">
      <div title={'Select-Config'}>
        <Container>
          <SpaceBetween size="l">
            <RadioGroup
              items={[
                {label: 'Create new configuration from scratch', value: 'new'},
                {label: 'Load existing configuration', value: 'load'},
              ]}
              value={newOrLoad}
              onChange={event => setNewOrLoad(event.detail.value)}
            />
            {newOrLoad === 'load' ?
              <Select
                selectedOption={selectedConfig}
                onChange={(event) => {
                  const selectedOption: OptionDefinition = event.detail.selectedOption;
                  setSelectedConfig(selectedOption);
                  populateForm(selectedOption);
                }}
                options={scanConfigurations}
                placeholder="Choose saved configuration"
              /> : <></>}
          </SpaceBetween>
        </Container>
      </div>

      <div title={'Edit-Config'}>
        <Form actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={() => navigate('/assessments/resource-based-policy')}>Cancel</Button>
            <Button variant="primary" loading={startingScan} onClick={validateConfigAndStartScan}>Start Scan</Button>
          </SpaceBetween>
        }>
          <Container
            header={
              <Header variant="h2">
                New Configuration
              </Header>
            }
          >
            <SpaceBetween size="l">
              <FormField label="Accounts to scan" stretch={true}>
                <RadioGroup
                  items={[
                    {label: 'All accounts in organization', value: 'all'},
                    {label: 'Accounts in organizational units specified below', value: 'org-units'},
                    {label: 'Accounts IDs specified below', value: 'listed'},
                  ]}
                  value={accountSelectionStrategy}
                  onChange={event => setAccountSelectionStrategy(event.detail.value)}
                />
              </FormField>
              {accountSelectionStrategy === 'listed' && <FormField
                description="List the account IDs of all AWS accounts you want to scan."
                constraintText="Specify account IDs separated with commas or put each on a new line."
                stretch={true}
                errorText={accountIdValidationError}
              >
                <Textarea
                    placeholder="111111222222,999999999999"
                    value={accountIdsToScan}
                    onChange={({detail}) => {
                    setAccountIdsToScan(detail.value);
                    if (accountIdValidationError) parseAccountIds(detail.value)
                  }}
                />
              </FormField>}
              {accountSelectionStrategy === 'org-units' && <FormField
                description="List the organizational unit IDs you want to scan."
                constraintText="Specify organizational unit IDs separated with commas or put each on a new line."
                stretch={true}
                errorText={organizationalUnitIdValidationError}
              >
                <Textarea
                  placeholder="ou-examplerootid111-exampleouid111,ou-examplerootid222-exampleouid222"
                  value={organizationalUnitIdsToScan}
                  onChange={({detail}) => {
                    setOrganizationalUnitIdsToScan(detail.value);
                    if (organizationalUnitIdValidationError) parseOrganizationalUnitIds(detail.value)
                  }}
                />
              </FormField>}
              <FormField
                label="Regions to scan"
                stretch={true}
              >
                <Multiselect
                  selectedOptions={selectedRegions}
                  onChange={(event) => {
                    const selectedRegions = event.detail.selectedOptions as RegionOption[];
                    setSelectedRegions(selectedRegions);
                  }}
                  deselectAriaLabel={e => `Remove ${e.label}`}
                  options={[
                    {
                      label: "Select All",
                      options: supportedRegions
                    }
                  ]}
                  placeholder="Choose regions"
                  selectedAriaLabel="Selected"
                />
              </FormField>
              <FormField
                label="Services to scan"
                stretch={true}
              >
                <Multiselect
                  selectedOptions={selectedServices}
                  onChange={(event) => {
                    const selectedServices = event.detail.selectedOptions as ServiceOption[];
                    setSelectedServices(selectedServices);
                  }}
                  deselectAriaLabel={e => `Remove ${e.label}`}
                  options={[
                    {
                      label: "Select All",
                      options: supportedServices
                    }
                  ]}
                  placeholder="Choose services"
                  selectedAriaLabel="Selected"
                />
              </FormField>

              <FormField
                label="Configuration name (optional)"
                description="Enter a descriptive name for this configuration to save it for future use"
                constraintText="Up to 64 characters, digits, hyphen or underscore"
                errorText={configNameValidationError}
                stretch={true}
              >
                <Input
                  onChange={event => {
                    setConfigName(event.detail.value);
                    if (configNameValidationError) validateConfigName(event.detail.value)
                  }}
                  value={configName}
                />
              </FormField>
            </SpaceBetween>
          </Container>
        </Form>
      </div>
    </SpaceBetween>
  </ContentLayout>
}