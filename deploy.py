"""
CivicPulse Deployer - Deploys the static site using Netlify's API.
"""
import http.client
import json
import os
import hashlib
import ssl
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_all_files(directory):
    """Get all files in directory with their paths relative to the project root."""
    files = {}
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in filenames:
            if filename == 'deploy.py':
                continue
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, directory).replace('\\', '/')
            with open(filepath, 'rb') as f:
                content = f.read()
            sha1 = hashlib.sha1(content).hexdigest()
            files['/' + relpath] = {
                'sha1': sha1,
                'content': content,
                'size': len(content)
            }
    return files

def deploy():
    print("CivicPulse Deployer")
    print("=" * 50)
    
    # Step 1: Collect files
    print("\nCollecting project files...")
    files = get_all_files(PROJECT_DIR)
    
    for path, info in files.items():
        print(f"  + {path} ({info['size']:,} bytes)")
    
    print(f"\nTotal files: {len(files)}")
    
    # Step 2: Create site with file digests
    print("\nDeploying to Netlify...")
    
    file_hashes = {path: info['sha1'] for path, info in files.items()}
    
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection("api.netlify.com", context=ctx)
    
    body = json.dumps({
        "files": file_hashes
    })
    
    headers = {
        "Content-Type": "application/json",
    }
    
    conn.request("POST", "/api/v1/sites", body=body, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    
    if resp.status not in (200, 201):
        print(f"ERROR: Failed to create site: {resp.status}")
        print(json.dumps(data, indent=2))
        return
    
    site_id = data.get('id', '')
    deploy_id = data.get('deploy_id', '')
    site_url = data.get('ssl_url') or data.get('url', '')
    subdomain = data.get('subdomain', '')
    required = data.get('required', [])
    
    print(f"  Site created: {site_url}")
    print(f"  Deploy ID: {deploy_id}")
    print(f"  Files to upload: {len(required)}")
    
    # Step 3: Upload required files
    uploaded = 0
    for sha in required:
        for path, info in files.items():
            if info['sha1'] == sha:
                print(f"  Uploading {path}...")
                upload_conn = http.client.HTTPSConnection("api.netlify.com", context=ctx)
                upload_conn.request(
                    "PUT",
                    f"/api/v1/deploys/{deploy_id}/files{path}",
                    body=info['content'],
                    headers={"Content-Type": "application/octet-stream"}
                )
                upload_resp = upload_conn.getresponse()
                upload_resp.read()
                upload_conn.close()
                
                if upload_resp.status in (200, 201):
                    uploaded += 1
                    print(f"     OK - Uploaded successfully")
                else:
                    print(f"     WARN - Status: {upload_resp.status}")
                break
    
    print(f"\nUploaded {uploaded}/{len(required)} files")
    print("\n" + "=" * 50)
    print(f"DEPLOYMENT COMPLETE!")
    print(f"=" * 50)
    print(f"\nYour site is live at:\n")
    print(f"   {site_url}")
    print(f"\nShare this link with anyone!")
    print()

if __name__ == '__main__':
    deploy()
