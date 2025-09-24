#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

from trusted_access_enabled_services.read_trusted_services import ReadTrustedServices
from trusted_access_enabled_services.trusted_services_repository import TrustedServicesRepository
from tests.test_utils.testdata_factory import trusted_access_create_request


def describe_trusted_services_pagination_bug_fix():

    def test_search_results_beyond_first_page(trusted_services_table):
        repository = TrustedServicesRepository()
        total_services = 1000
        
        services = []
        
        for i in range(int(total_services * 0.9)):
            service_name = f"standard-service-{i}.amazonaws.com"
            services.append(trusted_access_create_request(service_name))
        
        search_suffix = "special-suffix.amazonaws.com"
        for i in range(int(total_services * 0.1)):
            service_name = f"matching-service-{i}.{search_suffix}"
            services.append(trusted_access_create_request(service_name))
        
        repository.create_all(services)
        
        page_size = 200
        
        class_under_test = ReadTrustedServices()
        
        event_data = {
            'queryStringParameters': {
                'maxResults': str(page_size)
            }
        }
        
        first_page = class_under_test.read_trusted_access_enabled_services(APIGatewayProxyEvent(event_data), {})
        pagination = first_page['Pagination']
        
        all_found_services = first_page['Results'].copy()
        matching_services = [s for s in all_found_services if search_suffix in s['ServicePrincipal']]
        
        while pagination.get('nextToken') and pagination.get('hasMoreResults'):
            next_event_data = {
                'queryStringParameters': {
                    'maxResults': str(page_size),
                    'nextToken': pagination.get('nextToken')
                }
            }
            
            next_page = class_under_test.read_trusted_access_enabled_services(
                APIGatewayProxyEvent(next_event_data), {}
            )
            
            page_services = next_page['Results']
            all_found_services.extend(page_services)
            
            matching_services.extend([s for s in page_services if search_suffix in s['ServicePrincipal']])
            
            pagination = next_page['Pagination']
        
        assert len(all_found_services) == total_services
        
        assert len(matching_services) == int(total_services * 0.1)
        
        for service in matching_services:
            assert search_suffix in service['ServicePrincipal']

    def test_pagination_with_exact_boundary(trusted_services_table):
        repository = TrustedServicesRepository()
        
        services = []
        
        for i in range(100):
            service_name = f"standard-service-{i}.amazonaws.com"
            services.append(trusted_access_create_request(service_name))
        
        search_pattern = "target-pattern"
        for i in range(20):
            service_name = f"{search_pattern}-service-{i}.amazonaws.com"
            services.append(trusted_access_create_request(service_name))
        
        repository.create_all(services)
        
        class_under_test = ReadTrustedServices()
        
        first_event_data = {
            'queryStringParameters': {
                'maxResults': '100'
            }
        }
        
        first_page = class_under_test.read_trusted_access_enabled_services(
            APIGatewayProxyEvent(first_event_data), {}
        )
        
        first_page_results = first_page['Results']
        pagination = first_page['Pagination']
        
        first_page_matching = [s for s in first_page_results if search_pattern in s['ServicePrincipal']]
        
        second_page_matching = []
        if pagination.get('nextToken') and pagination.get('hasMoreResults'):
            next_event_data = {
                'queryStringParameters': {
                    'maxResults': '100',
                    'nextToken': pagination.get('nextToken')
                }
            }
            
            second_page = class_under_test.read_trusted_access_enabled_services(
                APIGatewayProxyEvent(next_event_data), {}
            )
            
            second_page_results = second_page['Results']
            
            second_page_matching = [s for s in second_page_results if search_pattern in s['ServicePrincipal']]
        
        total_matching = len(first_page_matching) + len(second_page_matching)
        assert total_matching == 20
        
        assert len(second_page_matching) > 0