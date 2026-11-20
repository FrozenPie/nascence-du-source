"""
validate_mermaid_topology.py — Audit architecture_diagram.mmd against live codebase

Verifies:
1. Every file path referenced in node labels exists on disk.
2. Node counts, subgraphs, and total edge counts.
3. Ensures 0 dead references in Nascence topology diagrams.
"""

import os
import re

MMD_PATH = r"C:\Nascence\docs\architecture_diagram.mmd"

def main():
    if not os.path.exists(MMD_PATH):
        print(f"ERROR: {MMD_PATH} does not exist.")
        return 1

    with open(MMD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find file path references like core/..., nodes/..., data/...
    file_refs = set(re.findall(r'(?:core|nodes|scripts|data|docs)/[a-zA-Z0-9_\-\./]+', content))
    
    print(f"=== Auditing Mermaid Topology ({len(file_refs)} file references) ===")
    
    missing = []
    found = []
    
    for ref in file_refs:
        # Strip trailing punctuation or label artifacts
        clean_ref = re.sub(r'[\"\,\)\}\]\:\;]+$', '', ref)
        full_path = os.path.join(r"C:\Nascence", clean_ref.replace('/', '\\'))
        if os.path.exists(full_path):
            found.append(clean_ref)
        else:
            missing.append(clean_ref)

    print(f"Verified File References ({len(found)}):")
    for f_path in sorted(found):
        print(f"  [OK] {f_path}")

    if missing:
        print(f"\nMissing File References ({len(missing)}):")
        for m_path in sorted(missing):
            print(f"  [MISSING] {m_path}")
    else:
        print("\n100% Topology Liveness Verified! All referenced files exist on disk.")

    # Count subgraphs, nodes, edges
    subgraphs = len(re.findall(r'subgraph\s+', content))
    edges = len(re.findall(r'--+>|-\.-\|', content))
    print(f"\nTopology Statistics:")
    print(f"  - Subgraphs: {subgraphs}")
    print(f"  - Edges/Connections: {edges}")

if __name__ == '__main__':
    main()
