#!/usr/bin/env python3
"""
Multi-Cloud AI Management Agent - Enhanced Setup Script
World-class AI agent for multi-cloud infrastructure management
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class MultiCloudSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "multi-cloud-agent" / "backend"
        self.frontend_dir = self.project_root / "multi-cloud-agent" / "frontend"
        
    def print_banner(self):
        print("=" * 60)
        print("🚀 MULTI-CLOUD AI MANAGEMENT AGENT 🚀")
        print("   World-Class AI for Cloud Infrastructure")
        print("=" * 60)
        print()
        
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("📋 Checking prerequisites...")
        
        requirements = {
            'python': ['python', '--version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
        }
        
        missing = []
        for tool, cmd in requirements.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {tool}: {result.stdout.strip()}")
                else:
                    missing.append(tool)
            except FileNotFoundError:
                missing.append(tool)
                
        if missing:
            print(f"  ❌ Missing: {', '.join(missing)}")
            print("  Please install the missing tools and try again.")
            return False
            
        print("  ✅ All prerequisites met!")
        return True
        
    def setup_backend(self):
        """Set up the Python backend"""
        print("\n🐍 Setting up Python backend...")
        
        os.chdir(self.backend_dir)
        
        # Create virtual environment
        if not (self.backend_dir / "venv").exists():
            print("  Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", "venv"])
            
        # Activate and install dependencies
        venv_python = self.get_venv_python()
        print("  Installing dependencies...")
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("  ✅ Backend setup complete!")
        
    def setup_frontend(self):
        """Set up the React frontend"""
        print("\n⚛️  Setting up React frontend...")
        
        os.chdir(self.frontend_dir)
        
        print("  Installing npm dependencies...")
        subprocess.run(["npm", "install"])
        
        print("  ✅ Frontend setup complete!")
        
    def create_env_files(self):
        """Create environment configuration files"""
        print("\n⚙️  Creating environment configuration...")
        
        # Backend .env
        backend_env = self.backend_dir / ".env"
        if not backend_env.exists():
            env_content = """# Multi-Cloud AI Agent Configuration
DATABASE_URL=sqlite:///./multi_cloud_agent.db
SESSION_SECRET=your-super-secret-key-change-in-production
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ENVIRONMENT=development
FORCE_HTTPS=false
"""
            backend_env.write_text(env_content)
            print("  ✅ Created backend .env file")
            
        # Frontend .env
        frontend_env = self.frontend_dir / ".env"
        if not frontend_env.exists():
            env_content = """REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id
"""
            frontend_env.write_text(env_content)
            print("  ✅ Created frontend .env file")
            
    def get_venv_python(self):
        """Get the path to the virtual environment Python executable"""
        if sys.platform == "win32":
            return str(self.backend_dir / "venv" / "Scripts" / "python.exe")
        else:
            return str(self.backend_dir / "venv" / "bin" / "python")
            
    def run_tests(self):
        """Run basic tests to ensure everything works"""
        print("\n🧪 Running basic tests...")
        
        os.chdir(self.backend_dir)
        venv_python = self.get_venv_python()
        
        # Test imports
        test_script = """
try:
    import fastapi
    import sqlalchemy
    import google.generativeai
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
"""
        
        result = subprocess.run([venv_python, "-c", test_script], capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode != 0:
            print("❌ Tests failed!")
            return False
            
        print("✅ All tests passed!")
        return True
        
    def show_next_steps(self):
        """Show next steps to the user"""
        print("\n🎉 Setup Complete! Next Steps:")
        print("\n1. Configure your API keys in the .env files:")
        print(f"   - Backend: {self.backend_dir}/.env")
        print(f"   - Frontend: {self.frontend_dir}/.env")
        
        print("\n2. Start the services:")
        print("   Backend:")
        print(f"   cd {self.backend_dir}")
        if sys.platform == "win32":
            print("   .\\venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        
        print("\n   Frontend (in a new terminal):")
        print(f"   cd {self.frontend_dir}")
        print("   npm start")
        
        print("\n3. Access the application at:")
        print("   🌐 Frontend: http://localhost:3000")
        print("   🔧 Backend API: http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
        
        print("\n4. Set up cloud credentials in the UI")
        
    def run(self):
        """Run the complete setup process"""
        try:
            self.print_banner()
            
            if not self.check_prerequisites():
                return False
                
            self.setup_backend()
            self.setup_frontend()
            self.create_env_files()
            
            if not self.run_tests():
                return False
                
            self.show_next_steps()
            return True
            
        except KeyboardInterrupt:
            print("\n❌ Setup cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            return False
        finally:
            os.chdir(self.project_root)

if __name__ == "__main__":
    setup = MultiCloudSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
