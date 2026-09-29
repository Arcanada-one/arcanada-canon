"""Offline architecture fitness: dependency layers and import-cycle detection."""
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {'model': set(), 'resolve': {'model'}, 'evaluate': {'model','resolve'},
           'load': {'model','resolve'}, 'shadow': {'model','load','evaluate'},
           '__init__': {'model','resolve','evaluate'}}
graph = {}
for path in sorted((ROOT/'engine/decisions').glob('*.py')):
    name = path.stem
    assert name in ALLOWED, f'unreviewed module: {name}'
    graph[name] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.level:
            assert node.level == 1 and node.module in ALLOWED[name], 'layer violation'
            graph[name].add(node.module)
        elif isinstance(node,(ast.Import,ast.ImportFrom)):
            modules = [n.name for n in node.names] if isinstance(node,ast.Import) else [node.module]
            assert all(m.split('.')[0] in sys.stdlib_module_names | {'jsonschema'} for m in modules), 'integration import'
def visit(node, ancestors):
    assert node not in ancestors, 'import cycle'
    for target in graph[node]:
        visit(target, ancestors | {node})
for node in graph:
    visit(node,set())
print(json.dumps({'verdict':'verified','scope':'static Python import layers; not runtime or semantic parity',
                  'edges':{k:sorted(v) for k,v in graph.items()}},sort_keys=True))
