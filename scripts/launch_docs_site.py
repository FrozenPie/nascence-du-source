"""
launch_docs_site.py — Launch Docusaurus web server for Nascence documentation site
"""

import os
import subprocess
import sys

docs_site_dir = r"C:\Nascence\docs_site"

def main():
    print(f"=== Booting Nascence Docusaurus Web Server ({docs_site_dir}) ===")
    
    # Check node_modules
    if not os.path.exists(os.path.join(docs_site_dir, 'node_modules')):
        print("node_modules not found. Installing dependencies via npm install...")
        subprocess.run("npm install", cwd=docs_site_dir, shell=True, check=True)

    build_dir = os.path.join(docs_site_dir, 'build')
    if os.path.exists(build_dir):
        print("Serving production build at http://localhost:3005 ...")
        subprocess.run("npm run serve -- --port 3005", cwd=docs_site_dir, shell=True)
    else:
        print("Serving dev server at http://localhost:3005 ...")
        subprocess.run("npm start -- --port 3005", cwd=docs_site_dir, shell=True)

if __name__ == '__main__':
    main()
