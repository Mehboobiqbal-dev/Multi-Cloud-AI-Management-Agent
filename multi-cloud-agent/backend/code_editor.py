from typing import Dict, Any, List, Optional
import os
import subprocess
import json
import logging
from pathlib import Path
# import git
# from git import Repo
import ast
import re
from dataclasses import dataclass

@dataclass
class CodeAnalysis:
    """Data class for code analysis results."""
    file_type: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    complexity_score: int
    lines_of_code: int
    issues: List[str]

class CodeEditor:
    """Advanced code editing and analysis tool."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
    
    def clone_repository(self, repo_url: str, local_path: str, branch: str = 'main') -> str:
        """Clone a Git repository to local path."""
        # Git functionality temporarily disabled for deployment
        return f"Git functionality is currently disabled. Cannot clone repository {repo_url}"
        # try:
        #     repo = Repo.clone_from(repo_url, local_path, branch=branch)
        #     return f"Successfully cloned repository {repo_url} to {local_path} (branch: {branch})"
        # except git.exc.GitCommandError as e:
        #     return f"Failed to clone repository: {str(e)}"
        # except Exception as e:
        #     return f"Error cloning repository: {str(e)}"

    def pull_repository(self, repo_path: str) -> str:
        """Pull latest changes from remote repository."""
        # Git functionality temporarily disabled for deployment
        return f"Git functionality is currently disabled. Cannot pull repository {repo_path}"
        # try:
        #     repo = Repo(repo_path)
        #     origin = repo.remotes.origin
        #     origin.pull()
        #     return f"Successfully pulled latest changes for repository at {repo_path}"
        # except Exception as e:
        #     return f"Failed to pull repository: {str(e)}"

    def analyze_repository_structure(self, repo_path: str) -> str:
        """Analyze repository structure and provide overview."""
        try:
            if not os.path.exists(repo_path):
                return f"Repository path {repo_path} does not exist"
            
            structure = {}
            total_files = 0
            total_lines = 0
            file_types = {}
            
            # Walk through repository
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common build/cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                level = root.replace(repo_path, '').count(os.sep)
                if level > 3:  # Limit depth
                    continue
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    ext = Path(file).suffix.lower()
                    
                    if ext in self.supported_extensions:
                        file_type = self.supported_extensions[ext]
                        file_types[file_type] = file_types.get(file_type, 0) + 1
                        total_files += 1
                        
                        # Count lines for code files
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                total_lines += lines
                        except:
                            pass
            
            # Generate summary
            result = f"Repository Analysis for {repo_path}:\n\n"
            result += f"Total Files: {total_files}\n"
            result += f"Total Lines of Code: {total_lines}\n\n"
            
            if file_types:
                result += "File Types:\n"
                for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                    result += f"  {file_type}: {count} files\n"
            
            # Check for common project files
            common_files = ['package.json', 'requirements.txt', 'Dockerfile', 'README.md', '.gitignore']
            found_files = []
            for file in common_files:
                if os.path.exists(os.path.join(repo_path, file)):
                    found_files.append(file)
            
            if found_files:
                result += f"\nProject Files Found: {', '.join(found_files)}\n"
            
            return result
            
        except Exception as e:
            return f"Failed to analyze repository structure: {str(e)}"

    def analyze_code_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a single code file for structure and complexity."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            ext = Path(file_path).suffix.lower()
            file_type = self.supported_extensions.get(ext, 'unknown')
            
            functions = []
            classes = []
            imports = []
            issues = []
            lines_of_code = len([line for line in content.split('\n') if line.strip()])
            
            # Python analysis using AST
            if ext == '.py':
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.append(alias.name)
                            else:
                                imports.append(node.module or '')
                except SyntaxError as e:
                    issues.append(f"Syntax error: {str(e)}")
            
            # JavaScript/TypeScript analysis using regex
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                # Simple regex-based analysis for JS/TS
                function_pattern = r'(?:function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|([a-zA-Z_$][a-zA-Z0-9_$]*)\s*[:=]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
                class_pattern = r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
                import_pattern1 = r'import\s+.*?from\s+"([^"]*)"'
                import_pattern2 = r"import\s+.*?from\s+\'([^\']*)\'"
                
                functions.extend([m.group(1) or m.group(2) for m in re.finditer(function_pattern, content) if m.group(1) or m.group(2)])
                classes.extend([m.group(1) for m in re.finditer(class_pattern, content)])
                imports.extend([m.group(1) for m in re.finditer(import_pattern1, content) if m.group(1)])
                imports.extend([m.group(1) for m in re.finditer(import_pattern2, content) if m.group(1)])
            
            # Calculate complexity score (simple heuristic)
            complexity_score = min(100, len(functions) * 2 + len(classes) * 3 + lines_of_code // 10)
            
            return CodeAnalysis(
                file_type=file_type,
                functions=functions,
                classes=classes,
                imports=imports,
                complexity_score=complexity_score,
                lines_of_code=lines_of_code,
                issues=issues
            )
            
        except Exception as e:
            return CodeAnalysis(
                file_type='unknown',
                functions=[],
                classes=[],
                imports=[],
                complexity_score=0,
                lines_of_code=0,
                issues=[f"Analysis failed: {str(e)}"]
            )
    
    def search_code_patterns(self, repo_path: str, pattern: str, file_extensions: List[str] = None) -> str:
        """Search for code patterns across repository."""
        try:
            if not file_extensions:
                file_extensions = list(self.supported_extensions.keys())
            
            matches = []
            
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common build/cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if any(file.endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            for i, line in enumerate(content.split('\n'), 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    rel_path = os.path.relpath(file_path, repo_path)
                                    matches.append(f"{rel_path}:{i}: {line.strip()}")
                        except:
                            continue
            
            if matches:
                result = f"Found {len(matches)} matches for pattern '{pattern}':\n\n"
                for match in matches[:20]:  # Limit to first 20 matches
                    result += f"  {match}\n"
                if len(matches) > 20:
                    result += f"  ... and {len(matches) - 20} more matches\n"
                return result
            else:
                return f"No matches found for pattern '{pattern}'"
                
        except Exception as e:
            return f"Failed to search code patterns: {str(e)}"
    
    def create_implementation_plan(self, repo_path: str, feature_description: str) -> str:
        """Create an implementation plan for a new feature."""
        try:
            # Analyze repository structure first
            structure_analysis = self.analyze_repository_structure(repo_path)
            
            plan = f"Implementation Plan for: {feature_description}\n\n"
            plan += "Repository Analysis:\n"
            plan += structure_analysis + "\n\n"
            
            plan += "Recommended Implementation Steps:\n"
            plan += "1. Analyze existing codebase patterns\n"
            plan += "2. Identify files that need modification\n"
            plan += "3. Create new files if necessary\n"
            plan += "4. Implement core functionality\n"
            plan += "5. Add error handling and validation\n"
            plan += "6. Write tests\n"
            plan += "7. Update documentation\n\n"
            
            plan += "Files to Consider:\n"
            # Look for main application files
            main_files = []
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                for file in files:
                    if file in ['main.py', 'app.py', 'index.js', 'server.js', 'main.js']:
                        main_files.append(os.path.join(root, file))
            
            if main_files:
                for file in main_files:
                    rel_path = os.path.relpath(file, repo_path)
                    plan += f"  - {rel_path} (main application file)\n"
            
            return plan
            
        except Exception as e:
            return f"Failed to create implementation plan: {str(e)}"
    
    def apply_code_changes(self, file_path: str, changes: List[Dict[str, Any]]) -> str:
        """Apply a series of code changes to a file."""
        try:
            if not os.path.exists(file_path):
                return f"File {file_path} does not exist"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Sort changes by line number in reverse order to avoid line number shifts
            changes = sorted(changes, key=lambda x: x.get('line', 0), reverse=True)
            
            applied_changes = []
            
            for change in changes:
                change_type = change.get('type', '').lower()
                line_num = change.get('line', 0)
                content = change.get('content', '')
                
                if change_type == 'insert':
                    if 0 <= line_num <= len(lines):
                        lines.insert(line_num, content + '\n')
                        applied_changes.append(f"Inserted at line {line_num}: {content[:50]}...")
                
                elif change_type == 'replace':
                    if 0 < line_num <= len(lines):
                        old_content = lines[line_num - 1].strip()
                        lines[line_num - 1] = content + '\n'
                        applied_changes.append(f"Replaced line {line_num}: {old_content[:30]}... -> {content[:30]}...")
                
                elif change_type == 'delete':
                    if 0 < line_num <= len(lines):
                        deleted_content = lines[line_num - 1].strip()
                        del lines[line_num - 1]
                        applied_changes.append(f"Deleted line {line_num}: {deleted_content[:50]}...")
            
            # Write changes back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            result = f"Applied {len(applied_changes)} changes to {file_path}:\n"
            for change in applied_changes:
                result += f"  - {change}\n"
            
            return result
            
        except Exception as e:
            return f"Failed to apply code changes: {str(e)}"
    
    def run_tests(self, repo_path: str, test_command: str = None) -> str:
        """Run tests in the repository."""
        try:
            os.chdir(repo_path)
            
            if not test_command:
                # Try to detect test command based on project type
                if os.path.exists('package.json'):
                    test_command = 'npm test'
                elif os.path.exists('requirements.txt') or os.path.exists('setup.py'):
                    test_command = 'python -m pytest'
                elif os.path.exists('Makefile'):
                    test_command = 'make test'
                else:
                    return "No test command specified and could not auto-detect test framework"
            
            result = subprocess.run(test_command, shell=True, capture_output=True, text=True, timeout=300)
            
            output = f"Test Command: {test_command}\n"
            output += f"Exit Code: {result.returncode}\n\n"
            
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n\n"
            
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            return output
            
        except subprocess.TimeoutExpired:
            return "Test execution timed out after 5 minutes"
        except Exception as e:
            return f"Failed to run tests: {str(e)}"

# Create global instance
code_editor = CodeEditor()