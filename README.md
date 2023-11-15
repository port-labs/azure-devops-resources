# Ingesting Azure Devops Resources


## Overview

In this example, you will create blueprints for `azure_devops_project`, `azure_devops_repository`, `azure_devops_pipeline` and `azure_devops_work_item` that ingests all projects, repositories, pipelines and work items from your Azure DevOps account. Also, you will add some python script to make API calls to Azure DevOps REST API and fetch data for your account. In addition to ingesting data via REST API, you will also configure webhooks to automatically update your entities in Port anytime an event occurs in your Azure DevOps account. For this example, you will subscribe to work items (i.e. create and update), pipelines (i.e run and job status change) and repository (i.e code commit) events.

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

To ingest data from your Azure DevOps account to Port, run the following commands: 

```bash
export PORT_CLIENT_ID=<ENTER CLIENT ID>
export PORT_CLIENT_SECRET=<ENTER CLIENT SECRET>
export AZURE_DEVOPS_ORG_ID=<ENTER AZURE DEVOPS ORGANIZATION ID>
export AZURE_DEVOPS_APP_PASSWORD=<ENTER AZURE DEVOPS APP PASSWORD>

git clone https://github.com/port-labs/azure-devops-resources.git

cd azure-devops-resources

pip install -r ./requirements.txt

python app.py

```

The list of variables required to run this script are:
- `PORT_CLIENT_ID`
- `PORT_CLIENT_SECRET`
- `AZURE_DEVOPS_ORG_ID` - Azure DevOps organization ID
- `AZURE_DEVOPS_APP_PASSWORD` - Azure DevOps app password 

Follow the documentation on how to [create an azure devops app password](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate?view=azure-devops&tabs=Windows). 


## Port Webhook Configuration

Webhooks are a great way to receive updates from third party platforms, and in this case, Azure DevOps. To [create an Azure Devops webhook](https://learn.microsoft.com/en-us/azure/devops/service-hooks/services/webhooks?view=azure-devops), you will first need to generate a webhook URL from Port.

Follow the following steps to create a webhook:
1. Navigate to the **Builder** section in Port and click **Data source**;
2. Under **Webhook** tab, click **Custom integration**;
3. In the **basic details** tab, you will be asked to provide information about your webhook such as the `title`, `identifier` `description`, and `icon`;
4. In the **integration configuration** tab, copy and pase the [webhook configuration file](./resources/webhook_configuration.json) into the **Map the data from the external system into Port** form;
5. Take note of the webhook `URL` provided by Port on this page. You will need this `URL` when subscribing to events in Azure DevOps;

6. Test the webhook configuration mapping and click on **Save**;
7. Under the **Advanced settings** tab, Azure Devops does not seem to support message validation via hashing the message with a shared secret. Leave this section blank and **Save** the configuration.

## Subscribing to Azure DevOps webhook
1. From your Azure DevOps account, open the project where you want to add the webhook;
2. Click **Project settings** on the left sidebar;
3. On the General section, select **Service hook** on the left sidebar;
4. Click the plus **+** button to create a webhook for the project; 
5. A pop up page will be shown. Select **Web Hooks** from the list and click **Next**;
6. Under **Trigger**, select the type of event you want to receive webhook notifications for. The example [webhook configuration](./resources/webhook_configuration.json) supports the following events:
    1. Code pushed
    2. Run state changed
    3. Run job state changed
    4. Run stage state changed
    4. Work item created
    5. Work item updated
7. Leave the **Filters** section unchanged and click **Next**;
8. On the final page (**Action Settings**), enter the value of the webhook `URL` you received after creating the webhook configuration in Port in the `URL` textbox;
9. Test your webhook subscription and click **Finish**


Follow [this documentation](https://learn.microsoft.com/en-us/azure/devops/service-hooks/events?toc=%2Fazure%2Fdevops%2Fmarketplace-extensibility%2Ftoc.json&view=azure-devops) to learn more about webhook events in Azure DevOps.

Done! any change that happens to your repository, work items or pipelines in Azure DevOps will trigger a webhook event to the webhook URL provided by Port. Port will parse the events according to the mapping and update the catalog entities accordingly.