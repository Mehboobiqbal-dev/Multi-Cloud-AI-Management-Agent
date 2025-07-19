import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError

def handle_aws(operation, resource, params=None):
    try:
        if resource == 'vm':
            if operation == 'list':
                try:
                    ec2 = boto3.client('ec2')
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
                    s3 = boto3.client('s3')
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

def handle_azure(operation, resource, params=None):
    # TODO: Add real Azure SDK logic
    if resource == 'vm':
        if operation == 'list':
            return {'result': 'Listed Azure VMs (mock)'}
        elif operation == 'create':
            return {'result': 'Created Azure VM (mock)'}
    if resource == 'storage':
        if operation == 'list':
            return {'result': 'Listed Azure Storage Accounts (mock)'}
        elif operation == 'create':
            return {'result': 'Created Azure Storage Account (mock)'}
    return {'result': f'Azure {operation} {resource} not implemented'}

def handle_gcp(operation, resource, params=None):
    # TODO: Add real GCP SDK logic
    if resource == 'vm':
        if operation == 'list':
            return {'result': 'Listed GCP Compute Engine VMs (mock)'}
        elif operation == 'create':
            return {'result': 'Created GCP Compute Engine VM (mock)'}
    if resource == 'storage':
        if operation == 'list':
            return {'result': 'Listed GCP Storage Buckets (mock)'}
        elif operation == 'create':
            return {'result': 'Created GCP Storage Bucket (mock)'}
    return {'result': f'GCP {operation} {resource} not implemented'}

def handle_clouds(intents, params=None):
    results = []
    for intent in intents:
        cloud = intent['cloud']
        operation = intent['operation']
        resource = intent['resource']
        if cloud == 'aws':
            result = handle_aws(operation, resource, params)
        elif cloud == 'azure':
            result = handle_azure(operation, resource, params)
        elif cloud == 'gcp':
            result = handle_gcp(operation, resource, params)
        else:
            result = {'error': 'Unknown cloud provider'}
        results.append({'cloud': cloud, 'operation': operation, 'resource': resource, 'result': result})
    return results