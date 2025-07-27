const https = require('https');

const BASE_URL = 'https://multi-cloud-ai-management-agent-production-acb4.up.railway.app';

const testEndpoint = (path) => {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'multi-cloud-ai-management-agent-production-acb4.up.railway.app',
      port: 443,
      path: path,
      method: 'GET',
      headers: {
        'User-Agent': 'Test-Script',
        'Accept': 'application/json'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode === 307 || res.statusCode === 308) {
          console.log(`🔄 ${path}: ${res.statusCode} - Redirect to: ${res.headers.location}`);
          // Follow the redirect
          const redirectUrl = res.headers.location;
          const redirectOptions = {
            hostname: 'multi-cloud-ai-management-agent-production-acb4.up.railway.app',
            port: 443,
            path: new URL(redirectUrl).pathname,
            method: 'GET',
            headers: {
              'User-Agent': 'Test-Script',
              'Accept': 'application/json'
            }
          };
          
          const redirectReq = https.request(redirectOptions, (redirectRes) => {
            let redirectData = '';
            redirectRes.on('data', (chunk) => {
              redirectData += chunk;
            });
            redirectRes.on('end', () => {
              console.log(`✅ ${path}: ${redirectRes.statusCode} - ${redirectData}`);
              resolve({ status: redirectRes.statusCode, data: redirectData });
            });
          });
          
          redirectReq.on('error', (error) => {
            console.log(`❌ ${path} (redirect): ${error.message}`);
            reject(error);
          });
          
          redirectReq.end();
        } else {
          console.log(`✅ ${path}: ${res.statusCode} - ${data}`);
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on('error', (error) => {
      console.log(`❌ ${path}: ${error.message}`);
      reject(error);
    });

    req.end();
  });
};

const testCORS = () => {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'multi-cloud-ai-management-agent-production-acb4.up.railway.app',
      port: 443,
      path: '/test-cors',
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    };

    const req = https.request(options, (res) => {
      if (res.statusCode === 307 || res.statusCode === 308) {
        console.log(`🔄 CORS Preflight: ${res.statusCode} - Redirect to: ${res.headers.location}`);
        // Follow the redirect for CORS test
        const redirectUrl = res.headers.location;
        const redirectOptions = {
          hostname: 'multi-cloud-ai-management-agent-production-acb4.up.railway.app',
          port: 443,
          path: new URL(redirectUrl).pathname,
          method: 'OPTIONS',
          headers: {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
          }
        };
        
        const redirectReq = https.request(redirectOptions, (redirectRes) => {
          console.log(`✅ CORS Preflight: ${redirectRes.statusCode}`);
          console.log(`   Access-Control-Allow-Origin: ${redirectRes.headers['access-control-allow-origin']}`);
          console.log(`   Access-Control-Allow-Methods: ${redirectRes.headers['access-control-allow-methods']}`);
          resolve();
        });
        
        redirectReq.on('error', (error) => {
          console.log(`❌ CORS Test (redirect): ${error.message}`);
          reject(error);
        });
        
        redirectReq.end();
      } else {
        console.log(`✅ CORS Preflight: ${res.statusCode}`);
        console.log(`   Access-Control-Allow-Origin: ${res.headers['access-control-allow-origin']}`);
        console.log(`   Access-Control-Allow-Methods: ${res.headers['access-control-allow-methods']}`);
        resolve();
      }
    });

    req.on('error', (error) => {
      console.log(`❌ CORS Test: ${error.message}`);
      reject(error);
    });

    req.end();
  });
};

async function runTests() {
  console.log('🧪 Testing Backend Endpoints...\n');
  
  try {
    await testEndpoint('/');
    await testEndpoint('/healthz');
    await testEndpoint('/test-cors');
    await testEndpoint('/api-test');
    await testCORS();
    
    console.log('\n🎉 All tests completed!');
    console.log('\n📝 Next steps:');
    console.log('1. Go to Railway dashboard and trigger a new deployment');
    console.log('2. Wait 2-3 minutes for deployment to complete');
    console.log('3. Run this test again to verify CORS is working');
  } catch (error) {
    console.log('\n❌ Some tests failed. Check Railway deployment.');
  }
}

runTests(); 