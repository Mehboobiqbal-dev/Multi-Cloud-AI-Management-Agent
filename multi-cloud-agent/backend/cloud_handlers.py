from abc import ABC, abstractmethod
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import AzureError
from google.oauth2 import service_account
from google.cloud import compute_v1, storage
import json

class CloudProvider(ABC):
    def __init__(self, creds):
        self.creds = creds

    def execute(self, operation, resource, params):
        method_name = f"{operation}_{resource}"
        method = getattr(self, method_name, self.unsupported_operation)
        return method(params)

    def unsupported_operation(self, params):
        return {"error": f"Unsupported operation for {self.__class__.__name__}"}

    @abstractmethod
    def list_vm(self, params):
        pass

    @abstractmethod
    def create_vm(self, params):
        pass

    @abstractmethod
    def delete_vm(self, params):
        pass

    @abstractmethod
    def list_storage(self, params):
        pass

    @abstractmethod
    def create_storage(self, params):
        pass

    @abstractmethod
    def delete_storage(self, params):
        pass

class AWSProvider(CloudProvider):
    def __init__(self, creds):
        super().__init__(creds)
        self.session = boto3.Session(
            aws_access_key_id=self.creds.get('access_key'),
            aws_secret_access_key=self.creds.get('secret_key'),
            region_name=creds.get('region', 'us-east-1')
        )

    def list_vm(self, params):
        try:
            ec2 = self.session.client('ec2')
            instances = ec2.describe_instances()
            instance_ids = [i['InstanceId'] for r in instances['Reservations'] for i in r['Instances']]
            return {'result': f'Listed AWS EC2 instances: {instance_ids}'}
        except NoCredentialsError:
            return {'error': 'AWS credentials not found'}
        except BotoCoreError as e:
            return {'error': f'AWS error: {str(e)}'}

    def create_vm(self, params):
        try:
            ec2 = self.session.client('ec2')
            instance_name = params.get('name', 'multi-cloud-agent-instance')
            
            # Basic parameters for a t2.micro instance with a default Amazon Linux 2 AMI
            instance = ec2.run_instances(
                ImageId='ami-0c55b159cbfafe1f0',  # A common Amazon Linux 2 AMI in us-east-1
                InstanceType='t2.micro',
                MinCount=1,
                MaxCount=1,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': instance_name}]
                    },
                ]
            )
            instance_id = instance['Instances'][0]['InstanceId']
            return {'result': f'Successfully initiated creation of AWS EC2 instance {instance_id} named {instance_name}'}
        except BotoCoreError as e:
            return {'error': f'AWS error: {str(e)}'}
        except Exception as e:
            return {'error': f'An unexpected error occurred: {str(e)}'}

    def delete_vm(self, params):
        instance_id = params.get('name') # Assuming name is the instance ID for now
        if not instance_id:
            return {'error': 'Instance ID or name must be provided for deletion.'}
        try:
            ec2 = self.session.client('ec2')
            response = ec2.terminate_instances(InstanceIds=[instance_id])
            return {'result': f'Successfully initiated termination of instance {instance_id}', 'details': response}
        except BotoCoreError as e:
            return {'error': f'AWS error: {str(e)}'}
        except Exception as e:
            return {'error': f'An unexpected error occurred: {str(e)}'}

    def list_storage(self, params):
        try:
            s3 = self.session.client('s3')
            buckets = s3.list_buckets()
            names = [b['Name'] for b in buckets['Buckets']]
            return {'result': f'Listed AWS S3 buckets: {names}'}
        except NoCredentialsError:
            return {'error': 'AWS credentials not found'}
        except BotoCoreError as e:
            return {'error': f'AWS error: {str(e)}'}

    def create_storage(self, params):
        return {'result': f"Created AWS S3 bucket with params: {params} (mock)"}

    def delete_storage(self, params):
        return {'result': f"Deleted AWS S3 bucket with params: {params} (mock)"}

class AzureProvider(CloudProvider):
    def __init__(self, creds):
        super().__init__(creds)
        if not all(k in self.creds for k in ['azure_subscription_id', 'azure_client_id', 'azure_client_secret', 'azure_tenant_id']):
            raise ValueError("Azure credentials incomplete")
        self.credential = ClientSecretCredential(
            self.creds['azure_tenant_id'],
            self.creds['azure_client_id'],
            self.creds['azure_client_secret']
        )
        self.subscription_id = self.creds['azure_subscription_id']

    def list_vm(self, params):
        try:
            compute_client = ComputeManagementClient(self.credential, self.subscription_id)
            vms = compute_client.virtual_machines.list_all()
            vm_names = [vm.name for vm in vms]
            return {'result': f'Listed Azure VMs: {vm_names}'}
        except AzureError as e:
            return {'error': f'Azure error: {str(e)}'}

    def create_vm(self, params):
        return {'result': f"Created Azure VM with params: {params} (mock)"}

    def delete_vm(self, params):
        return {'result': f"Deleted Azure VM with params: {params} (mock)"}

    def list_storage(self, params):
        try:
            storage_client = StorageManagementClient(self.credential, self.subscription_id)
            accounts = storage_client.storage_accounts.list()
            account_names = [acc.name for acc in accounts]
            return {'result': f'Listed Azure Storage Accounts: {account_names}'}
        except AzureError as e:
            return {'error': f'Azure error: {str(e)}'}

    def create_storage(self, params):
        return {'result': f"Created Azure Storage Account with params: {params} (mock)"}

    def delete_storage(self, params):
        return {'result': f"Deleted Azure Storage Account with params: {params} (mock)"}

class GCPProvider(CloudProvider):
    def __init__(self, creds):
        super().__init__(creds)
        if not all(k in self.creds for k in ['gcp_project_id', 'gcp_credentials_json']):
            raise ValueError("GCP credentials incomplete")
        
        credentials_info = json.loads(self.creds['gcp_credentials_json'])
        self.credentials = service_account.Credentials.from_service_account_info(credentials_info)
        self.project_id = self.creds['gcp_project_id']

    def list_vm(self, params):
        try:
            instance_client = compute_v1.InstancesClient(credentials=self.credentials)
            agg_list = instance_client.aggregated_list(project=self.project_id)
            vm_names = []
            for zone, resp in agg_list:
                for inst in resp.instances or []:
                    vm_names.append(inst.name)
            return {'result': f'Listed GCP Compute Engine VMs: {vm_names}'}
        except Exception as e:
            return {'error': f'GCP error: {str(e)}'}

    def create_vm(self, params):
        return {'result': f"Created GCP VM with params: {params} (mock)"}

    def delete_vm(self, params):
        return {'result': f"Deleted GCP VM with params: {params} (mock)"}

    def list_storage(self, params):
        try:
            storage_client = storage.Client(credentials=self.credentials, project=self.project_id)
            buckets = list(storage_client.list_buckets())
            bucket_names = [b.name for b in buckets]
            return {'result': f'Listed GCP Storage Buckets: {bucket_names}'}
        except Exception as e:
            return {'error': f'GCP error: {str(e)}'}

    def create_storage(self, params):
        return {'result': f"Created GCP Storage Bucket with params: {params} (mock)"}

    def delete_storage(self, params):
        return {'result': f"Deleted GCP Storage Bucket with params: {params} (mock)"}

PROVIDER_MAP = {
    'aws': AWSProvider,
    'azure': AzureProvider,
    'gcp': GCPProvider,
}

def handle_clouds(intents, user_creds):
    results = []
    for intent in intents:
        cloud = intent['cloud']
        operation = intent['operation']
        resource = intent['resource']
        params = intent.get('params', {})
        
        if cloud not in PROVIDER_MAP:
            results.append({'cloud': cloud, 'operation': operation, 'resource': resource, 'result': {'error': 'Unknown cloud provider'}})
            continue

        creds = user_creds.get(cloud, {})
        try:
            provider_class = PROVIDER_MAP[cloud]
            provider = provider_class(creds)
            result = provider.execute(operation, resource, params)
        except ValueError as e:
            result = {'error': str(e)}
        except Exception as e:
            result = {'error': f'An unexpected error occurred with {cloud}: {str(e)}'}
            
        results.append({'cloud': cloud, 'operation': operation, 'resource': resource, 'result': result})
    return results
