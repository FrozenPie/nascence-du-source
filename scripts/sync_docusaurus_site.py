"""
sync_docusaurus_site.py — Copy and sync all 338 Markdown files from C:\\Nascence\\docs\\ into C:\\Nascence\\docs_site\\docs\\ with homepage slug routing.
"""

import os
import shutil
import glob

source_docs = r"C:\Nascence\docs"
target_docs = r"C:\Nascence\docs_site\docs"

os.makedirs(target_docs, exist_ok=True)

md_files = glob.glob(os.path.join(source_docs, '**', '*.md'), recursive=True)

print(f"Syncing {len(md_files)} Markdown files into Docusaurus site...")

copied = 0
for src_path in md_files:
    rel_path = os.path.relpath(src_path, source_docs)
    dest_path = os.path.join(target_docs, rel_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # If this is System_Overview.md, add frontmatter with slug: /
    if rel_path == 'System_Overview.md':
        if not content.startswith('---'):
            frontmatter = "---\nslug: /\nid: System_Overview\ntitle: Nascence 渡 — Master System Overview\nsidebar_label: 🏛️ Master System Overview (Aug 2026 · Claude)\n---\n\n"
            content = frontmatter + content
        elif 'slug:' not in content:
            content = content.replace('---\n', '---\nslug: /\n', 1)
    elif rel_path == 'System_Overview_Antigravity.md':
        if not content.startswith('---'):
            frontmatter = "---\nid: System_Overview_Antigravity\ntitle: Nascence 渡 — System Overview (Antigravity Build 2.0 · Oct 2026)\nsidebar_label: 🚀 System Overview (Oct 2026 · Build 2.0)\n---\n\n"
            content = frontmatter + content

    # Write to target
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)
    copied += 1

print(f"Successfully synced {copied} Markdown files into {target_docs}!")
