knowledge = {
    'aws': {
        'vm': {
            'list': 'List all EC2 instances in your AWS account. Example: "List all EC2 instances on AWS". Requires AWS credentials.',
            'create': 'Create a new EC2 instance. Example: "Create a t2.micro EC2 instance on AWS". Requires instance type, AMI, etc.'
        },
        'storage': {
            'list': 'List all S3 buckets in your AWS account. Example: "List all S3 buckets on AWS". Requires AWS credentials.',
            'create': 'Create a new S3 bucket. Example: "Create a storage bucket on AWS". Requires bucket name.'
        }
    },
    'azure': {
        'vm': {
            'list': 'List all Virtual Machines in your Azure subscription. Example: "List all VMs in Azure". Requires Azure credentials.',
            'create': 'Create a new Azure VM. Example: "Create a VM in Azure". Requires VM size, image, etc.'
        },
        'storage': {
            'list': 'List all Storage Accounts in your Azure subscription. Example: "List all storage accounts in Azure". Requires Azure credentials.',
            'create': 'Create a new Storage Account. Example: "Create a storage account in Azure". Requires account name.'
        }
    },
    'gcp': {
        'vm': {
            'list': 'List all Compute Engine VMs in your GCP project. Example: "List all VMs in GCP". Requires GCP credentials.',
            'create': 'Create a new Compute Engine VM. Example: "Create a VM in GCP". Requires machine type, image, etc.'
        },
        'storage': {
            'list': 'List all Storage Buckets in your GCP project. Example: "List all storage buckets in GCP". Requires GCP credentials.',
            'create': 'Create a new Storage Bucket. Example: "Create a storage bucket in GCP". Requires bucket name.'
        }
    }
}

error_explanations = {
    'credentials': 'Credentials for the selected cloud provider are missing or invalid. Please configure your credentials.',
    'not_implemented': 'This operation is not yet implemented for the selected cloud provider.',
    'unknown': 'Unknown error occurred. Please check your prompt and try again.'
}

def get_operation_doc(cloud, resource, operation):
    doc = knowledge.get(cloud, {}).get(resource, {}).get(operation, 'No documentation available.')
    return doc

def get_error_explanation(error_type):
    return error_explanations.get(error_type, error_explanations['unknown'])