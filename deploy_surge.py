"""
Deploy CivicPulse to Surge.sh
Run: python deploy_surge.py
"""
import subprocess
import os
import sys
import random
import string

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_BIN = os.path.join(PROJECT_DIR, '.nodeenv', 'Scripts')

def deploy():
    # Generate a unique subdomain
    suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
    domain = f"civicpulse-{suffix}.surge.sh"
    
    env = os.environ.copy()
    env['PATH'] = NODE_BIN + ';' + env.get('PATH', '')
    
    print(f"Deploying to: {domain}")
    print(f"Project dir: {PROJECT_DIR}")
    
    # Run surge
    result = subprocess.run(
        ['cmd', '/c', 'npx.cmd', '-y', 'surge', PROJECT_DIR, domain],
        env=env,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    if result.returncode == 0:
        print(f"\nSite is live at: https://{domain}")
    else:
        print("\nDeployment may have failed. Check output above.")

if __name__ == '__main__':
    deploy()
