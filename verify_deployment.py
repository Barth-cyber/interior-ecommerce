#!/usr/bin/env python3
"""
Render Deployment Verification Script
Checks if your Flask app is ready for deployment to Render
Run this before deploying to catch common issues
"""

import os
import sys
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def check_required_files():
    """Check if all required deployment files exist"""
    print_header("1. Checking Required Files")
    
    required_files = {
        'Procfile': 'Deployment startup config',
        'requirements.txt': 'Python dependencies',
        'application.py': 'Flask entry point',
        'admin/app.py': 'Flask app instance',
        '.gitignore': 'Git ignore patterns',
    }
    
    all_ok = True
    for filename, description in required_files.items():
        if Path(filename).exists():
            print_success(f"{filename} - {description}")
        else:
            print_error(f"{filename} - {description} - NOT FOUND")
            all_ok = False
    
    return all_ok

def check_procfile():
    """Verify Procfile has correct commands"""
    print_header("2. Checking Procfile Configuration")
    
    procfile_path = Path('Procfile')
    if not procfile_path.exists():
        print_error("Procfile not found")
        return False
    
    content = procfile_path.read_text().strip()
    
    # Check for required elements
    checks = {
        'has_gunicorn': 'gunicorn' in content,
        'has_app_ref': 'application:app' in content,
        'has_port_binding': '0.0.0.0' in content,
        'has_port_var': '$PORT' in content,
    }
    
    all_ok = True
    if checks['has_gunicorn']:
        print_success("Uses gunicorn (correct server)")
    else:
        print_error("Missing 'gunicorn' in Procfile")
        all_ok = False
    
    if checks['has_app_ref']:
        print_success("Correct entry point (application:app)")
    else:
        print_error("Wrong entry point - should be 'application:app'")
        all_ok = False
    
    if checks['has_port_binding']:
        print_success("Binds to 0.0.0.0 (all interfaces)")
    else:
        print_error("Missing 0.0.0.0 binding")
        all_ok = False
    
    if checks['has_port_var']:
        print_success("Uses $PORT environment variable")
    else:
        print_error("Hardcoded port - should use $PORT")
        all_ok = False
    
    print(f"\nProcfile content:\n{Colors.BLUE}{content}{Colors.RESET}")
    return all_ok

def check_requirements():
    """Verify requirements.txt is valid"""
    print_header("3. Checking requirements.txt")
    
    req_path = Path('requirements.txt')
    if not req_path.exists():
        print_error("requirements.txt not found")
        return False
    
    try:
        content = req_path.read_text(encoding='utf-8-sig').strip().split('\n')
    except:
        content = req_path.read_text(encoding='utf-8', errors='ignore').strip().split('\n')
    
    print_success(f"Found {len(content)} packages")
    
    # Check for essential packages (case-insensitive, with version specifiers)
    essential = {
        'Flask': False,
        'gunicorn': False,
    }
    
    for line in content:
        line_lower = line.lower().strip()
        for pkg in essential:
            if line_lower.startswith(pkg.lower()):
                essential[pkg] = True
                # Extract version if present
                if '==' in line:
                    version = line.split('==')[1]
                    print_success(f"Includes {pkg} ({version})")
                else:
                    print_success(f"Includes {pkg}")
    
    all_ok = all(essential.values())
    
    if not all_ok:
        missing = [pkg for pkg, found in essential.items() if not found]
        for pkg in missing:
            print_error(f"Missing required package: {pkg}")
    
    # Check for problematic packages
    if any('flask-cors' in line.lower() for line in content):
        print_success("CORS is configured (good for API)")
    
    # Python version check
    python_reqs = [line for line in content if 'python' in line.lower() or 'py' in line]
    if python_reqs:
        print_warning(f"Python version requirement: {python_reqs[0]}")
    
    return all_ok

def check_application_entry():
    """Verify application.py is correct"""
    print_header("4. Checking application.py Entry Point")
    
    app_path = Path('application.py')
    if not app_path.exists():
        print_error("application.py not found")
        return False
    
    content = app_path.read_text()
    
    checks = {
        'imports_app': 'from admin.app import app' in content or 'from admin import app' in content,
        'has_if_name_main': 'if __name__' in content,
        'binds_0000': '0.0.0.0' in content,
    }
    
    if checks['imports_app']:
        print_success("Correctly imports Flask app from admin/app.py")
    else:
        print_error("Doesn't import Flask app correctly")
        return False
    
    if checks['has_if_name_main']:
        print_success("Has 'if __name__ == __main__' guard")
    else:
        print_warning("Missing 'if __name__ == __main__' guard")
    
    if checks['binds_0000']:
        print_success("Binds to 0.0.0.0 (correct)")
    else:
        print_error("Not binding to 0.0.0.0")
    
    print(f"\nFirst 10 lines of application.py:\n{Colors.BLUE}")
    for line in content.split('\n')[:10]:
        print(line)
    print(Colors.RESET)
    
    return all(checks.values())

def check_admin_app():
    """Verify admin/app.py Flask configuration"""
    print_header("5. Checking admin/app.py Flask App")
    
    admin_app_path = Path('admin/app.py')
    if not admin_app_path.exists():
        print_error("admin/app.py not found")
        return False
    
    content = admin_app_path.read_text()
    
    checks = {
        'creates_app': 'Flask(__name__)' in content,
        'has_app_var': 'app = ' in content,
    }
    
    if checks['creates_app']:
        print_success("Creates Flask app instance")
    else:
        print_error("Doesn't create Flask app")
        return False
    
    if checks['has_app_var']:
        print_success("Assigns to 'app' variable")
    else:
        print_error("Flask app not assigned to 'app' variable")
        return False
    
    if 'CORS' in content:
        print_success("CORS is enabled (good for API)")
    
    return all(checks.values())

def check_port_hardcoding():
    """Check for hardcoded localhost/port references"""
    print_header("6. Checking for Hardcoded Ports/Localhost")
    
    py_files = list(Path('.').glob('**/*.py'))
    warnings_found = []
    
    hardcoded_checks = [
        ('localhost', 'Hardcoded localhost'),
        ('127.0.0.1', 'Hardcoded 127.0.0.1'),
        (':5000', 'Hardcoded port 5000'),
        (':3000', 'Hardcoded port 3000'),
        (':8000', 'Hardcoded port 8000'),
    ]
    
    for py_file in py_files:
        if '.venv' in str(py_file):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
        except:
            continue
            
        for pattern, description in hardcoded_checks:
            if pattern in content:
                # Skip if it's in a comment or docstring
                if f"# {pattern}" not in content and f'"{pattern}"' not in content:
                    warnings_found.append((py_file, pattern, description))
    
    if warnings_found:
        print_warning(f"Found {len(warnings_found)} potential hardcoded values:")
        for file, pattern, desc in warnings_found:
            print_warning(f"  {file}: {desc} ({pattern})")
        print_warning("These might not work on Render. Use environment variables instead.")
        return False
    else:
        print_success("No hardcoded ports or localhost found")
        return True

def check_git_status():
    """Verify git is configured correctly"""
    print_header("7. Checking Git Configuration")
    
    # Check if .git exists
    if not Path('.git').exists():
        print_error("Not a git repository (.git not found)")
        return False
    
    print_success("Git repository initialized")
    
    # Check for remote
    try:
        with open('.git/config', 'r') as f:
            config = f.read()
            if 'interior-ecommerce' in config:
                print_success("GitHub remote configured (interior-ecommerce)")
            elif 'github.com' in config:
                print_warning("GitHub remote exists but name doesn't match")
            else:
                print_error("No GitHub remote found")
                return False
    except:
        print_warning("Could not read git config")
    
    return True

def check_environment_vars():
    """List required environment variables"""
    print_header("8. Required Environment Variables for Render")
    
    required_vars = {
        'ADMIN_SECRET_KEY': 'Random secure key for sessions',
        'ADMIN_USERNAME': 'Admin login username (optional)',
        'ADMIN_COOKIE_SECURE': 'Set to "true" for production',
        'PYTHONUNBUFFERED': 'Set to "true" for real-time logs',
    }
    
    print(f"{Colors.YELLOW}Add these to Render Dashboard → Settings → Environment:{Colors.RESET}\n")
    
    for var, description in required_vars.items():
        print(f"{Colors.BLUE}{var}{Colors.RESET}")
        print(f"  Description: {description}")
        if var == 'ADMIN_SECRET_KEY':
            print(f"  Example: a7f8e3b2c9d1f4a6e8b0c2d4f6a8e0c2d4f6a8e0c2d4f6a8e0")
        elif var == 'ADMIN_COOKIE_SECURE':
            print(f"  Value: true")
        elif var == 'PYTHONUNBUFFERED':
            print(f"  Value: true")
        print()
    
    return True

def check_static_files():
    """Verify static files are in correct locations"""
    print_header("9. Checking Static Files")
    
    static_dirs = {
        'static': 'Main static directory',
        'admin/static': 'Admin static directory (optional)',
    }
    
    all_ok = True
    for dir_name, description in static_dirs.items():
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = list(dir_path.glob('*'))
            print_success(f"{dir_name}/ exists - {description} ({len(files)} items)")
        else:
            print_warning(f"{dir_name}/ not found - {description}")
            all_ok = False
    
    # Check for interior.html
    html_locations = ['interior.html', 'static/interior.html', 'admin/static/interior.html']
    found = False
    for location in html_locations:
        if Path(location).exists():
            print_success(f"Found interior.html at {location}")
            found = True
            break
    
    if not found:
        print_warning("interior.html not found - ensure Flask serves it from a route")
    
    return all_ok

def generate_summary(results):
    """Generate deployment readiness summary"""
    print_header("Deployment Readiness Summary")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Checks passed: {Colors.GREEN}{passed}/{total}{Colors.RESET}")
    
    if percentage >= 90:
        print_success(f"Your app is {Colors.GREEN}{percentage:.0f}% ready for Render deployment!")
        print(f"\n{Colors.GREEN}Next steps:{Colors.RESET}")
        print("1. Go to https://render.com and sign up with GitHub")
        print("2. Create a new Web Service")
        print("3. Select interior-ecommerce repository")
        print("4. Add environment variables (ADMIN_SECRET_KEY, etc.)")
        print("5. Click 'Create Web Service' and wait 2-3 minutes")
        return True
    elif percentage >= 70:
        print_warning(f"Your app is {percentage:.0f}% ready - fix warnings above before deploying")
        return False
    else:
        print_error(f"Your app is only {percentage:.0f}% ready - fix errors above before deploying")
        return False

def main():
    print(f"\n{Colors.BLUE}╔{'═'*58}╗")
    print(f"║ Render Deployment Verification Script                 ║")
    print(f"║ Interior Ecommerce Flask Application                  ║")
    print(f"╚{'═'*58}╝{Colors.RESET}\n")
    
    results = {}
    
    results['files'] = check_required_files()
    results['procfile'] = check_procfile()
    results['requirements'] = check_requirements()
    results['app_entry'] = check_application_entry()
    results['admin_app'] = check_admin_app()
    results['hardcoding'] = check_port_hardcoding()
    results['git'] = check_git_status()
    check_environment_vars()  # Just informational
    results['static'] = check_static_files()
    
    ready = generate_summary(results)
    
    return 0 if ready else 1

if __name__ == '__main__':
    sys.exit(main())
