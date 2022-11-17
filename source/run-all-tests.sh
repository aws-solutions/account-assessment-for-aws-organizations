#!/bin/bash
#
# This script runs all tests for the root CDK project, as well as any microservices, Lambda functions, or dependency
# source code packages. These include unit tests, integration tests, and snapshot tests.
#
# This script is called by the ../initialize-repo.sh file and the buildspec.yml file. It is important that this script
# be tested and validated to ensure that all available test fixtures are run.
#
# The if/then blocks are for error handling. They will cause the script to stop executing if an error is thrown from the
# node process running the test case(s). Removing them or not using them for additional calls with result in the
# script continuing to execute despite an error being thrown.

[ "$DEBUG" == 'true' ] && set -x
set -e

setup_python_env() {
	if [ -d "./.venv-test" ]; then
		echo "Reusing already setup python venv in ./.venv-test. Delete ./.venv-test if you want a fresh one created."
		return
	fi

    echo "Setting up python venv"
	python3 -m venv .venv-test
	echo "Initiating virtual environment"
	source .venv-test/bin/activate

    echo "Installing python packages"
    # install test dependencies in the python virtual environment
	pip3 install -r testing_requirements.txt
	pip3 install -r requirements.txt

	echo "deactivate virtual environment"
	deactivate
}

run_python_tests() {
	local component_path=$1

	echo "------------------------------------------------------------------------------"
	echo "[Test] Run python unit test with coverage for $component_path"
	echo "------------------------------------------------------------------------------"
	cd $component_path

	if [ "${CLEAN:-true}" = "true" ]; then
        rm -fr .venv-test
    fi

	setup_python_env

	echo "Initiating virtual environment"
	source .venv-test/bin/activate

	coverage_report_path="$source_dir/lambda/coverage.xml"
	echo "coverage report path set to $coverage_report_path"

	# Use -vv for debugging
	python3 -m pytest tests --cov "$component_path" --cov-config="$component_path/.coveragerc" --cov-report=term-missing --cov-report "xml:$coverage_report_path" --cov-report "html:$component_path/coverage"

    # The pytest --cov with its parameters and .coveragerc generates a xml cov-report with `coverage/sources` list
    # with absolute path for the source directories. To avoid dependencies of tools (such as SonarQube) on different
    # absolute paths for source directories, this substitution is used to convert each absolute source directory
    # path to the corresponding project relative path. The $source_dir holds the absolute path for source directory.
    sed -i -e "s,<source>$source_dir,<source>source,g" $coverage_report_path

	echo "deactivate virtual environment"
	deactivate

	if [ "${CLEAN:-true}" = "true" ]; then
		rm -fr .venv-test
		rm .coverage
		rm -fr .pytest_cache
		rm -fr __pycache__ test/__pycache__
	fi
}

run_webui_tests() {
  	local component_path=$1

    echo "------------------------------------------------------------------------------"
    echo "[Test] Run javascript unit test with coverage for $component_path"
    echo "------------------------------------------------------------------------------"

 	cd $component_path
	npm install
  npm run test:ci # run test:ci rather than test to avoid the pipeline getting stuck in watch mode
}

run_cdk_project_tests() {
	local component_path=$1
    local component_name=solutions-constructs

	echo "------------------------------------------------------------------------------"
	echo "[Test] $component_name"
	echo "------------------------------------------------------------------------------"
    cd $component_path

	# install and build for unit testing
	npm install

	## Option to suppress the Override Warning messages while synthesizing using CDK
	# export overrideWarningsEnabled=false

	# run unit tests
	npm run test -- -u
}

# Run unit tests
echo "Running unit tests"

# Get reference for source folder
source_dir="$(cd $PWD/../source; pwd -P)"

# Test the CDK project
## Create mock zip file for cdk to find needed asset
mkdir -p ../deployment/regional-s3-assets/
touch ../deployment/regional-s3-assets/lambda.zip
run_cdk_project_tests $source_dir || true

# Test the WebUI project
run_webui_tests $source_dir/webui || true

# Test the attached Lambda functions
run_python_tests $source_dir/lambda

# Return to the source/ level
cd $source_dir