import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import AzureError
import os

def handle_aws(operation, resource, creds, params=None):
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, NoCredentialsError
        if resource == 'vm':
            if operation == 'list':
                try:
                    session = boto3.Session(
                        aws_access_key_id=creds.get('access_key'),
                        aws_secret_access_key=creds.get('secret_key'),
                    )
                    ec2 = session.client('ec2')
                    instances = ec2.describe_instances()
                    instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
                    return {'result': f'Listed AWS EC2 instances: {instance_ids}'}
                except NoCredentialsError:
                    return {'error': 'AWS credentials not found'}
                except BotoCoreError as e:
                    return {'error': f'AWS error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created AWS EC2 instance (mock)'}
        if resource == 'storage':
            if operation == 'list':
                try:
                    session = boto3.Session(
                        aws_access_key_id=creds.get('access_key'),
                        aws_secret_access_key=creds.get('secret_key'),
                    )
                    s3 = session.client('s3')
                    buckets = s3.list_buckets()
                    names = [b['Name'] for b in buckets['Buckets']]
                    return {'result': f'Listed AWS S3 buckets: {names}'}
                except NoCredentialsError:
                    return {'error': 'AWS credentials not found'}
                except BotoCoreError as e:
                    return {'error': f'AWS error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created AWS S3 bucket (mock)'}
        return {'result': f'AWS {operation} {resource} not implemented'}
    except Exception as e:
        return {'error': f'Unexpected AWS error: {str(e)}'}

def handle_azure(operation, resource, creds, params=None):
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.compute import ComputeManagementClient
        from azure.mgmt.storage import StorageManagementClient
        from azure.core.exceptions import AzureError
        subscription_id = creds.get('azure_subscription_id')
        client_id = creds.get('azure_client_id')
        client_secret = creds.get('azure_client_secret')
        tenant_id = creds.get('azure_tenant_id')
        if not (subscription_id and client_id and client_secret and tenant_id):
            return {'error': 'Azure credentials incomplete'}
        credential = ClientSecretCredential(tenant_id, client_id, client_secret)
        if resource == 'vm':
            if operation == 'list':
                try:
                    compute_client = ComputeManagementClient(credential, subscription_id)
                    vms = compute_client.virtual_machines.list_all()
                    vm_names = [vm.name for vm in vms]
                    return {'result': f'Listed Azure VMs: {vm_names}'}
                except AzureError as e:
                    return {'error': f'Azure error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created Azure VM (mock)'}
        if resource == 'storage':
            if operation == 'list':
                try:
                    storage_client = StorageManagementClient(credential, subscription_id)
                    accounts = storage_client.storage_accounts.list()
                    account_names = [acc.name for acc in accounts]
                    return {'result': f'Listed Azure Storage Accounts: {account_names}'}
                except AzureError as e:
                    return {'error': f'Azure error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created Azure Storage Account (mock)'}
        return {'result': f'Azure {operation} {resource} not implemented'}
    except Exception as e:
        return {'error': f'Unexpected Azure error: {str(e)}'}

def handle_gcp(operation, resource, creds, params=None):
    try:
        import json
        from google.cloud import compute_v1, storage
        project = creds.get('gcp_project_id')
        credentials_json = creds.get('gcp_credentials_json')
        if not (project and credentials_json):
            return {'error': 'GCP credentials incomplete'}
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write(credentials_json)
            cred_path = f.name
        if resource == 'vm':
            if operation == 'list':
                try:
                    instance_client = compute_v1.InstancesClient.from_service_account_file(cred_path)
                    agg_list = instance_client.aggregated_list(project=project)
                    vm_names = []
                    for zone, resp in agg_list:
                        for inst in resp.instances or []:
                            vm_names.append(inst.name)
                    return {'result': f'Listed GCP Compute Engine VMs: {vm_names}'}
                except Exception as e:
                    return {'error': f'GCP error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created GCP Compute Engine VM (mock)'}
        if resource == 'storage':
            if operation == 'list':
                try:
                    storage_client = storage.Client.from_service_account_json(cred_path, project=project)
                    buckets = list(storage_client.list_buckets())
                    bucket_names = [b.name for b in buckets]
                    return {'result': f'Listed GCP Storage Buckets: {bucket_names}'}
                except Exception as e:
                    return {'error': f'GCP error: {str(e)}'}
            elif operation == 'create':
                return {'result': 'Created GCP Storage Bucket (mock)'}
        return {'result': f'GCP {operation} {resource} not implemented'}
    except Exception as e:
        return {'error': f'Unexpected GCP error: {str(e)}'}

def handle_clouds(intents, user_creds, params=None):
    results = []
    for intent in intents:
        cloud = intent['cloud']
        operation = intent['operation']
        resource = intent['resource']
        creds = user_creds.get(cloud, {})
        if cloud == 'aws':
            result = handle_aws(operation, resource, creds, params)
        elif cloud == 'azure':
            result = handle_azure(operation, resource, creds, params)
        elif cloud == 'gcp':
            result = handle_gcp(operation, resource, creds, params)
        else:
            result = {'error': 'Unknown cloud provider'}
        results.append({'cloud': cloud, 'operation': operation, 'resource': resource, 'result': result})
    return results