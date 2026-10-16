import os
import sys
import json
import hashlib
from pathlib import Path
from collections import defaultdict

def scan_files(dir_path):
    p = Path(dir_path)
    if not p.exists():
        return []
    res = []
    for f in p.rglob('*'):
        if f.is_file():
            if any(part.startswith('.') or part == '__pycache__' for part in f.parts):
                continue
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            rel = os.path.relpath(f, '.').replace('\\', '/')
            res.append({
                'path': rel,
                'name': f.name,
                'size': f.stat().st_size,
                'sha256': h,
                'dir': os.path.relpath(f.parent, '.').replace('\\', '/')
            })
    return res

json_projects = [
    Path('guardados/recursos_temp/prueba_imagen.json'),
    Path('docs/ejemplos/disenos/ejemplo_espejo_12.json')
]

project_refs = defaultdict(set)
all_refs = set()

for pj in json_projects:
    if not pj.exists():
        continue
    data = json.loads(pj.read_text(encoding='utf-8'))
    pj_rel = os.path.relpath(pj, '.').replace('\\', '/')
    disenos = data.get('disenos', {})
    for sec_name, sec_diseno in disenos.items():
        if isinstance(sec_diseno, dict):
            for capa in sec_diseno.get('capas', []):
                arch = capa.get('archivo')
                if arch:
                    project_refs[pj_rel].add(arch)
                    all_refs.add(arch)

guardados_files = scan_files('guardados')
docs_files = scan_files('docs/ejemplos')
all_files = guardados_files + docs_files

by_hash = defaultdict(list)
for f in all_files:
    by_hash[f['sha256']].append(f)

total_count = len(all_files)
total_bytes = sum(f['size'] for f in all_files)

duplicate_bytes = 0
for h, flist in by_hash.items():
    if len(flist) > 1:
        duplicate_bytes += flist[0]['size'] * (len(flist) - 1)

for f in all_files:
    is_ref = f['name'] in all_refs
    f['is_referenced'] = is_ref
    f['referencing_projects'] = [pj for pj, refs in project_refs.items() if f['name'] in refs]

ref_files = [f for f in all_files if f['is_referenced']]
unref_files = [f for f in all_files if not f['is_referenced']]

ref_bytes = sum(f['size'] for f in ref_files)
unref_bytes = sum(f['size'] for f in unref_files)

lines = []
lines.append('# Informe de Recursos y Análisis de Duplicados')
lines.append('')
lines.append('Este informe detalla el inventario de archivos en `guardados/` y `docs/ejemplos/`, identificando referencias en proyectos JSON, archivos sin uso y grupos de duplicados por hash SHA-256.')
lines.append('')
lines.append('## 1. Resumen Ejecutivo')
lines.append('')
lines.append('| Métrica | Valor |')
lines.append('|---|---|')
lines.append(f'| **Total de archivos analizados** | {total_count} |')
lines.append(f'| **Espacio total ocupado** | {total_bytes / (1024*1024):.2f} MB ({total_bytes:,} bytes) |')
lines.append(f'| **Espacio duplicado** | {duplicate_bytes / (1024*1024):.2f} MB ({duplicate_bytes:,} bytes) |')
lines.append(f'| **Archivos referenciados por proyectos** | {len(ref_files)} ({ref_bytes / (1024*1024):.2f} MB) |')
lines.append(f'| **Archivos sin uso (no referenciados)** | {len(unref_files)} ({unref_bytes / (1024*1024):.2f} MB) |')
lines.append(f'| **Grupos de archivos con contenido idéntico (SHA-256)** | {sum(1 for fl in by_hash.values() if len(fl) > 1)} |')
lines.append('')
lines.append('### Proyectos JSON analizados')
for pj_rel, refs in sorted(project_refs.items()):
    lines.append(f'- **`{pj_rel}`**: {len(refs)} archivos referenciados en capas:')
    for r in sorted(refs):
        found = any(f['name'] == r for f in all_files)
        status = 'presente en disco' if found else 'no encontrado en recursos locales'
        lines.append(f'  - `{r}` ({status})')
lines.append('')
lines.append('## 2. Grupos de Archivos Duplicados (Mismo SHA-256)')
lines.append('')
lines.append('A continuación se listan los grupos donde 2 o más archivos tienen exactamente el mismo hash SHA-256:')
lines.append('')

dup_groups = sorted([fl for fl in by_hash.values() if len(fl) > 1], key=lambda g: g[0]['size'] * (len(g)-1), reverse=True)
for i, g in enumerate(dup_groups, 1):
    h = g[0]['sha256']
    sz = g[0]['size']
    wasted = sz * (len(g) - 1)
    lines.append(f'### Grupo {i}: SHA-256 `{h[:16]}...` ({len(g)} copias, {sz:,} bytes c/u, desperdicio: {wasted:,} bytes)')
    lines.append('| Archivo | Referenciado | Proyectos que lo citan |')
    lines.append('|---|---|---|')
    for item in g:
        ref_str = 'Sí' if item['is_referenced'] else 'No'
        projs = ', '.join(f'`{p}`' for p in item['referencing_projects']) if item['referencing_projects'] else '-'
        lines.append(f'| `{item["path"]}` | {ref_str} | {projs} |')
    lines.append('')

lines.append('## 3. Inventario Completo de Archivos')
lines.append('')
lines.append('| Ruta Relativa | Tamaño (bytes) | SHA-256 | Referenciado |')
lines.append('|---|---|---|---|')
for f in sorted(all_files, key=lambda x: x['path']):
    ref_str = 'Sí' if f['is_referenced'] else 'No'
    lines.append(f'| `{f["path"]}` | {f["size"]:,} | `{f["sha256"][:16]}...` | {ref_str} |')

out_path = Path('docs/informe_recursos.md')
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text('\n'.join(lines), encoding='utf-8')

print('RESUMEN_METRICAS:')
print(f'NUM_ARCHIVOS: {total_count}')
print(f'MB_TOTALES: {total_bytes / (1024*1024):.2f}')
print(f'MB_DUPLICADOS: {duplicate_bytes / (1024*1024):.2f}')
print(f'MB_SIN_USO: {unref_bytes / (1024*1024):.2f}')
