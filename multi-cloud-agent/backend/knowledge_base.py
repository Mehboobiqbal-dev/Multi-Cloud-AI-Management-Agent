knowledge = {
    'aws': {
        'vm': {
            'list': 'List all EC2 instances in your AWS account.',
            'create': 'Create a new EC2 instance. Requires instance type, AMI, etc.'
        },
        'storage': {
            'list': 'List all S3 buckets in your AWS account.',
            'create': 'Create a new S3 bucket. Requires bucket name.'
        }
    },
    'azure': {
        'vm': {
            'list': 'List all Virtual Machines in your Azure subscription.',
            'create': 'Create a new Azure VM. Requires VM size, image, etc.'
        },
        'storage': {
            'list': 'List all Storage Accounts in your Azure subscription.',
            'create': 'Create a new Storage Account. Requires account name.'
        }
    },
    'gcp': {
        'vm': {
            'list': 'List all Compute Engine VMs in your GCP project.',
            'create': 'Create a new Compute Engine VM. Requires machine type, image, etc.'
        },
        'storage': {
            'list': 'List all Storage Buckets in your GCP project.',
            'create': 'Create a new Storage Bucket. Requires bucket name.'
        }
    }
}

def get_operation_doc(cloud, resource, operation):
    return knowledge.get(cloud, {}).get(resource, {}).get(operation, 'No documentation available.')