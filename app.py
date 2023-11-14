## Import the needed libraries
import requests
from requests.auth import HTTPBasicAuth
from decouple import config
from loguru import logger
from typing import Any
import time

# Get environment variables using the config object or os.environ["KEY"]
# These are the credentials passed by the variables of your pipeline to your tasks and in to your env

PORT_CLIENT_ID = config("PORT_CLIENT_ID")
PORT_CLIENT_SECRET = config("PORT_CLIENT_SECRET")
AZURE_DEVOPS_ORG_ID = config("AZURE_DEVOPS_ORG_ID")
AZURE_DEVOPS_APP_PASSWORD = config("AZURE_DEVOPS_APP_PASSWORD")
AZURE_DEVOPS_API_URL = "https://dev.azure.com"
PORT_API_URL = "https://api.getport.io/v1"
PAGE_SIZE = 100

## According to https://learn.microsoft.com/en-us/azure/devops/integrate/concepts/rate-limits?view=azure-devops
RATE_LIMIT = 200  # Maximum number of requests allowed per 5 minutes sliding window 
RATE_PERIOD = 500  # Rate limit reset period in seconds (5 minutes)

# Initialize rate limiting variables
request_count = 0
rate_limit_start = time.time()

## Get Port Access Token
credentials = {'clientId': PORT_CLIENT_ID, 'clientSecret': PORT_CLIENT_SECRET}
token_response = requests.post(f'{PORT_API_URL}/auth/access_token', json=credentials)
access_token = token_response.json()['accessToken']

# You can now use the value in access_token when making further requests
port_headers = {
	'Authorization': f'Bearer {access_token}'
}

## Azure auth password https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows
azure_devops_basic_auth = HTTPBasicAuth(username='', password=AZURE_DEVOPS_APP_PASSWORD)


def add_entity_to_port(blueprint_id, entity_object):
    response = requests.post(f'{PORT_API_URL}/blueprints/{blueprint_id}/entities?upsert=true&merge=true', json=entity_object, headers=port_headers)
    logger.info(response.json())

def get_azure_query_data(path: str, query_body: dict[str, Any]):
    logger.info(f"Requesting query data for {path}")

    url = f"{AZURE_DEVOPS_API_URL}/{AZURE_DEVOPS_ORG_ID}/{path}"
    response = requests.post(url=url, json=query_body, auth=azure_devops_basic_auth)
    logger.info("Query data retrieved successfully")
    return response.json()

def get_paginated_resource(path: str):
    logger.info(f"Requesting data for {path}")

    global request_count, rate_limit_start

    # Check if we've exceeded the rate limit, and if so, wait until the reset period is over
    if request_count >= RATE_LIMIT:
        elapsed_time = time.time() - rate_limit_start
        if elapsed_time < RATE_PERIOD:
            sleep_time = RATE_PERIOD - elapsed_time
            time.sleep(sleep_time)

        # Reset the rate limiting variables
        request_count = 0
        rate_limit_start = time.time()

    url = f"{AZURE_DEVOPS_API_URL}/{AZURE_DEVOPS_ORG_ID}/{path}"
    continuation_token = None

    pagination_params: dict[str, Any] = {"$top": PAGE_SIZE}

    while True:
        try:
            if continuation_token:
                pagination_params["continuationToken"] = continuation_token

            response = requests.get(url=url, auth=azure_devops_basic_auth, params=pagination_params)
            response.raise_for_status()
            page_json = response.json()
            request_count += 1
            batch_data = page_json["value"]
            yield batch_data

            # Check for continuation token in response header
            continuation_token = response.headers.get("x-ms-continuationtoken")

            # Break the loop if there is no more data
            if not continuation_token:
                break
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error with info: {e}")
            raise
    logger.info(f"Successfully fetched paginated data for {path}")


def process_project_entities(projects_data: list[dict[str, Any]]):
    blueprint_id = "azure_devops_project"

    for project in projects_data:

        entity = {
            "identifier": project["id"],
            "title": project["name"],
            "properties": {
                "description": project["description"],
                "url": project["url"],
                "visibility": project["visibility"],
                "last_updated_time": project["lastUpdateTime"]
            },
            "relations": {}
        }
        add_entity_to_port(blueprint_id=blueprint_id, entity_object=entity)


def process_repository_entities(repository_data: list[dict[str, Any]]):
    blueprint_id = "azure_devops_repository"

    for repo in repository_data:

        entity = {
        "identifier": repo["id"],
        "title": repo["name"],
        "properties": {
            "url": repo["url"],
            "default_branch": repo.get("defaultBranch"),
            "is_disabled": repo["isDisabled"]
        },
        "relations": {
            "project": repo["project"]["id"]
        }
        }
        add_entity_to_port(blueprint_id=blueprint_id, entity_object=entity)


def process_pipeline_entities(pipeline_data: list[dict[str, Any]], project_id: str):
    blueprint_id = "azure_devops_pipeline"

    for pipeline in pipeline_data:

        entity = {
            "identifier": str(pipeline["id"]),
            "title": pipeline["name"],
            "properties": {
                "url": pipeline["url"],
                "revision": pipeline["revision"],
            },
            "relations": {
                "project": project_id
            }
        }
        add_entity_to_port(blueprint_id=blueprint_id, entity_object=entity)


def process_work_item_entities(work_item_data: list[dict[str, Any]], project_id: str):
    blueprint_id = "azure_devops_work_item"

    for work_item in work_item_data:

        entity = {
            "identifier": str(work_item["id"]),
            "title": work_item["fields"]["System.Title"],
           "properties": {
                "url": work_item["url"],
                "revision": work_item["rev"],
                "type": work_item["fields"]["System.WorkItemType"],
                "state": work_item["fields"]["System.State"],
                "created_date": work_item["fields"]["System.CreatedDate"],
                "created_by": work_item["fields"]["System.CreatedBy"]["displayName"],
                "updated_date": work_item["fields"]["System.ChangedDate"],
                "priority": work_item["fields"]["Microsoft.VSTS.Common.Priority"]
            },
            "relations": {
                "project": project_id
            }
        }
        add_entity_to_port(blueprint_id=blueprint_id, entity_object=entity)


def get_repositories(project: dict[str, Any]):
    repository_path = f"{project['id']}/_apis/git/repositories?api-version=7.1-preview.1"
    for repositories_batch in get_paginated_resource(path=repository_path):
        logger.info(f"received repositories batch with size {len(repositories_batch)}")
        process_repository_entities(repository_data=repositories_batch)


def get_pipelines(project: dict[str, Any]):
    pipeline_path = f"{project['id']}/_apis/pipelines?api-version=7.1-preview.1"
    for pipelines_batch in get_paginated_resource(path=pipeline_path):
        logger.info(f"received pipelines batch with size {len(pipelines_batch)}")
        process_pipeline_entities(pipeline_data=pipelines_batch, project_id=project["id"])

def get_work_items(project: dict[str, Any]):
    query_body = { "query": f"SELECT [Id] from WorkItems Where [System.AreaPath] = '{project['name']}'" }
    query_path = f"{project['id']}/_apis/wit/wiql?api-version=7.1-preview.2"
    query_response = get_azure_query_data(path=query_path, query_body=query_body)
    work_items = [item["id"] for item in query_response["workItems"]]

    batch_size = 200 ## The work item API can only process up to 200 IDs at a time

    # Process work items in batches
    for i in range(0, len(work_items), batch_size):
        batch = work_items[i:i + batch_size]
        ids_str = ",".join(map(str, batch ))

        work_items_path = f"{project['id']}/_apis/wit/workitems?ids={ids_str}&api-version=7.1-preview.3"
        for work_items_batch in get_paginated_resource(path=work_items_path):
            logger.info(f"received work items batch with size {len(work_items_batch)}")
            process_work_item_entities(work_item_data=work_items_batch, project_id=project["id"])


if __name__ == "__main__":
    ## Loop through all the projects and fetch their related resources [repositories, pipelines and work items]
    project_path = f"_apis/projects?api-version=7.1-preview.4"
    for projects_batch in get_paginated_resource(path=project_path):
        logger.info(f"received projects batch with size {len(projects_batch)}")
        process_project_entities(projects_data=projects_batch)

        for project in projects_batch:
            get_repositories(project=project)
            get_pipelines(project=project)
            get_work_items(project=project)
