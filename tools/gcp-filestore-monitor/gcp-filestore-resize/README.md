# GCP Filestore Autosize

The purpose of this script is to allow the increment of Filestore Volumes when they reach a predefined capacity threshold. The calculation of the capacity is done in a different project (gcp-filestore-monitor).

The function expects a POST request with some information of the volumes that need to be increased.

## Environment Variables

| Name        | Description |
|LOGLEVEL     | Logging level for the function (INFO, WARN, ERROR...). Optional.|

Additional configuration can be found inside the config.json file. It contains details regarding the different Filestore Tiers.

## Permissions

The cloud function itself, requires a Service Account with the following permissions:

| Permission  | Scope       |
| ----------- | ----------- |
|resourcemanager.projects.list | Organization/Folder scope|
|resourcemanager.projects.get | Organization/Folder scope|
|file.instances.get | Organization/Folder scope|
|file.instances.list | Organization/Folder scope|
|file.instances.update| Organization/Folder scope|

## Execution

The POST request expects a json list of elements with information regarding the filestores that needs to be updated.

- name: Full name of the filestore instance that needs to be updated.
- capacity: Current capacity of the filestore instance (before update). A validation is made inside the process to make sure the capacity has not been updated, this to avoid triggering concurrent updates to a single instance.
- increase_percentage: How much the volume capacity needs to be increased. For Enterprise and High Scale Tiers which need to be increased by a certain amount, the code will make it's best effort to match the next available size which exceeds the provided increase percentage.

```
[
    {
		"name": "projects/{project}/locations/{location}/instances/{instance_name}", 
		"capacity": 1024, 
		"increase_percentage": 10
	}
]
```

For running on local environment, below command needs to be executed. It will return an endpoint which can be called to trigger the code.

```
python -m venv .venv
.venv\scripts\activate
pip install -r requirements.txt
functions-framework --target filestore_resize --port 8081
```

In a different session, call the endpoint returned by the previous command.
```
curl -X POST -H "Content-Type:application/json" -d '[{\"name\": <fs_instance_name>, \"capacity\": <fs_current_capacity>, \"increase_percentage\": <desired_increase_percentage>}]' <url>
```

## Example
Creates and deployes the cloud function. If function already exists, code gets redeployed. Must be executed on the functions root directory in order to push the code.

```
gcloud functions deploy {function_name} --runtime python39 --trigger-http --entry-point filestore_resize --region {region} --service-account {service_account}
```

If the function needs to be redeployed without modifying the environment variables a shorter version of the command can be executed.

```
gcloud functions deploy {function_name} --runtime python39 --trigger-http --entry-point filestore_resize --region {region}
```