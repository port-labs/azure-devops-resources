# Ingesting Azure Devops Resources


## Overview

In this example, you will create blueprints for `azure_devops_project`, `azure_devops_repository`, `azure_devops_pipeline` and `azure_devops_work_item` that ingests all projects, repositories, pipelines and work items from your Azure DevOps account. Also, you will add some python script to make API calls to Azure DevOps REST API and fetch data for your account.

## Getting started

Log in to your Port account and create the following blueprints:

### Project blueprint
Create the project blueprint in Port [using this json file](./resources/project.json)

### Repository blueprint
Create the repository blueprint in Port [using this json file](./resources/repository.json)

### Pipeline blueprint
Create the pipeline blueprint in Port [using this json file](./resources/pipeline.json)

### Work item blueprint
Create the work item blueprint in Port [using this json file](./resources/work_item.json)


### Running the python script

Run the python script provided in `app.py` file to ingest data from your Azure DevOps account.

The list of variables required to run this script are:
- `PORT_CLIENT_ID`
- `PORT_CLIENT_SECRET`
- `AZURE_DEVOPS_ORG_ID`
- `AZURE_DEVOPS_APP_PASSWORD`

Follow the documentation on how to [create an azure devops app password](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows). 


