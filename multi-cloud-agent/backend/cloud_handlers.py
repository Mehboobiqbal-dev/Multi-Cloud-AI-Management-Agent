def handle_aws(operation, resource, params=None):
    if resource == 'vm':
        if operation == 'list':
            return {'result': 'Listed AWS EC2 instances (mock)'}
        elif operation == 'create':
            return {'result': 'Created AWS EC2 instance (mock)'}
    if resource == 'storage':
        if operation == 'list':
            return {'result': 'Listed AWS S3 buckets (mock)'}
        elif operation == 'create':
            return {'result': 'Created AWS S3 bucket (mock)'}
    return {'result': f'AWS {operation} {resource} not implemented'}

def handle_azure(operation, resource, params=None):
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

def handle_cloud(cloud, operation, resource, params=None):
    if cloud == 'aws':
        return handle_aws(operation, resource, params)
    elif cloud == 'azure':
        return handle_azure(operation, resource, params)
    elif cloud == 'gcp':
        return handle_gcp(operation, resource, params)
    else:
        return {'result': 'Unknown cloud provider'}