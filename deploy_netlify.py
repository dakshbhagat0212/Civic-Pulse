"""
Deploy CivicPulse using Netlify Drop (zip upload via API).
Uses the Netlify deploy API which allows creating anonymous sites.
"""
import http.client
import json
import os
import hashlib
import ssl
import sys
import io
import zipfile
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {'.nodeenv', '.git', '__pycache__', 'node_modules'}
SKIP_FILES = {'deploy.py', 'deploy_surge.py', 'deploy_netlify.py'}

def create_zip():
    """Create a zip of the project files."""
    zip_path = os.path.join(tempfile.gettempdir(), 'civicpulse_deploy.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f in SKIP_FILES or f.endswith('.py'):
                    continue
                filepath = os.path.join(root, f)
                arcname = os.path.relpath(filepath, PROJECT_DIR)
                zf.write(filepath, arcname)
                print(f"  Added: {arcname}")
    return zip_path

def deploy():
    print("CivicPulse Netlify Deployer")
    print("=" * 50)
    
    print("\nCreating deployment package...")
    zip_path = create_zip()
    zip_size = os.path.getsize(zip_path)
    print(f"Package size: {zip_size:,} bytes")
    
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    
    print("\nUploading to Netlify...")
    
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection("api.netlify.com", context=ctx)
    
    headers = {
        "Content-Type": "application/zip",
        "Content-Length": str(len(zip_data))
    }
    
    conn.request("POST", "/api/v1/sites", body=zip_data, headers=headers)
    resp = conn.getresponse()
    resp_data = resp.read().decode('utf-8')
    conn.close()
    
    print(f"Response status: {resp.status}")
    
    if resp.status in (200, 201):
        data = json.loads(resp_data)
        site_url = data.get('ssl_url') or data.get('url', '')
        site_id = data.get('id', '')
        subdomain = data.get('subdomain', '')
        
        print("\n" + "=" * 50)
        print("DEPLOYMENT SUCCESSFUL!")
        print("=" * 50)
        print(f"\nYour site is live at:\n")
        print(f"   {site_url}")
        print(f"\nSite ID: {site_id}")
        print(f"Subdomain: {subdomain}")
        print(f"\nShare this link with anyone!")
    else:
        print(f"ERROR: Deployment failed with status {resp.status}")
        print(resp_data[:500])
    
    # Clean up
    os.remove(zip_path)

if __name__ == '__main__':
    deploy()
