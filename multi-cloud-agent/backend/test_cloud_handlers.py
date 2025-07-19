import unittest
import os
from cloud_handlers import handle_azure, handle_gcp

class TestCloudHandlers(unittest.TestCase):
    def test_azure_vm_list_no_creds(self):
        # Unset subscription id to simulate missing creds
        if 'AZURE_SUBSCRIPTION_ID' in os.environ:
            del os.environ['AZURE_SUBSCRIPTION_ID']
        result = handle_azure('list', 'vm')
        self.assertIn('error', result)
        self.assertIn('subscription ID', result['error'])

    def test_gcp_vm_list_no_creds(self):
        # Unset project to simulate missing creds
        if 'GOOGLE_CLOUD_PROJECT' in os.environ:
            del os.environ['GOOGLE_CLOUD_PROJECT']
        result = handle_gcp('list', 'vm')
        self.assertIn('error', result)
        self.assertIn('project not set', result['error'])

if __name__ == '__main__':
    unittest.main()