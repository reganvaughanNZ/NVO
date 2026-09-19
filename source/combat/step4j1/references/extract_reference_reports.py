"""Read the three user-supplied DOCX reports without changing their bytes.

Extracts every paragraph (including table cells) from document, note, header,
footer and comment stories, plus relationship targets. This is text review,
not a claim about Word page rendering or the factual accuracy of the reports.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
INPUT = Path('C:/Users/regan/Downloads')
NAMES = (
    'FNV_Armor_Clothing_NVO_Report.docx',
    'FNV_Armored_Creature_Variants_NVO_Report.docx',
    'FNV_Weapons_and_NVO_Report.docx',
)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
P = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def text_of(paragraph):
    out = []
    for node in paragraph.iter():
        if node.tag in (W + 't', W + 'delText', W + 'instrText'):
            out.append(node.text or '')
        elif node.tag == W + 'tab':
            out.append('\t')
        elif node.tag in (W + 'br', W + 'cr'):
            out.append('\n')
        elif node.tag in (W + 'footnoteReference', W + 'endnoteReference'):
            out.append('[' + node.tag.split('}')[-1] + ':' + node.get(W + 'id', '') + ']')
    return ''.join(out)


receipts = []
for name in NAMES:
    source = INPUT / name
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    stories, relationships, lines = [], {}, []
    counts = dict(paragraphs=0, nonempty_paragraphs=0, tables=0, table_rows=0,
                  table_cells=0, footnotes=0, endnotes=0,
                  nonempty_footnote_paragraphs=0, nonempty_endnote_paragraphs=0,
                  drawing_nodes=0, alt_chunks=0)
    with zipfile.ZipFile(source) as archive:
        for part in sorted(archive.namelist()):
            if part.startswith('word/') and part.endswith('.rels'):
                rels = ET.fromstring(archive.read(part))
                relationships[part] = [dict(node.attrib) for node in rels.findall(P + 'Relationship')]
        story_names = [part for part in archive.namelist() if re.fullmatch(
            r'word/(document|footnotes|endnotes|comments|header\d+|footer\d+)\.xml', part)]
        story_names.sort(key=lambda x: (x != 'word/document.xml', x))
        for part in story_names:
            tree = ET.fromstring(archive.read(part))
            parent = {child: node for node in tree.iter() for child in node}
            tables = list(tree.iter(W + 'tbl'))
            table_ids = {id(node): i + 1 for i, node in enumerate(tables)}
            records = []
            lines.append('\n=== ' + part + ' ===')
            for number, para in enumerate(tree.iter(W + 'p'), 1):
                content = text_of(para)
                path, node = [], para
                while node in parent:
                    node = parent[node]
                    if node.tag == W + 'tbl':
                        path.append('table=' + str(table_ids[id(node)]))
                    elif node.tag in (W + 'tr', W + 'tc'):
                        siblings = [child for child in parent[node] if child.tag == node.tag]
                        path.append(node.tag.split('}')[-1] + '=' + str(siblings.index(node) + 1))
                    elif node.tag in (W + 'footnote', W + 'endnote', W + 'comment'):
                        path.append(node.tag.split('}')[-1] + '=' + node.get(W + 'id', ''))
                style = para.find(W + 'pPr/' + W + 'pStyle')
                record = {'paragraph': number, 'location': '/'.join(reversed(path)),
                          'style': style.get(W + 'val') if style is not None else None,
                          'text': content}
                records.append(record)
                lines.append(f'[{part} p{number}' + (' ' + record['location'] if path else '') + '] ' + content)
            story_counts = {'paragraphs': len(records),
                            'nonempty_paragraphs': sum(bool(p['text'].strip()) for p in records),
                            'tables': len(tables),
                            'table_rows': len(list(tree.iter(W + 'tr'))),
                            'table_cells': len(list(tree.iter(W + 'tc'))),
                            'footnotes': len(list(tree.iter(W + 'footnote'))),
                            'endnotes': len(list(tree.iter(W + 'endnote'))),
                            'nonempty_footnote_paragraphs': sum(bool(p['text'].strip()) for p in records if 'footnote=' in p['location']),
                            'nonempty_endnote_paragraphs': sum(bool(p['text'].strip()) for p in records if 'endnote=' in p['location']),
                            'drawing_nodes': len(list(tree.iter(W + 'drawing'))),
                            'alt_chunks': len(list(tree.iter(W + 'altChunk')))}
            for key, value in story_counts.items():
                counts[key] += value
            stories.append({'part': part, 'counts': story_counts, 'paragraphs': records})
    text_path = ROOT / (source.stem + '.txt')
    json_path = ROOT / (source.stem + '.json')
    text_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    json_path.write_text(json.dumps({'source_name': name, 'source_sha256': digest,
                                    'stories': stories, 'relationships': relationships},
                                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    receipts.append({'source': str(source), 'bytes': len(original), 'sha256': digest,
                     'counts': counts, 'story_parts': story_names,
                     'external_relationships': [entry for entries in relationships.values() for entry in entries if entry.get('TargetMode') == 'External'],
                     'extracted_text': text_path.name,
                     'extracted_text_sha256': hashlib.sha256(text_path.read_bytes()).hexdigest(),
                     'extracted_json': json_path.name,
                     'extracted_json_sha256': hashlib.sha256(json_path.read_bytes()).hexdigest()})

receipt = {'extracted_utc': datetime.now(timezone.utc).isoformat(),
           'method': 'zipfile plus ElementTree; all paragraphs including table cells and available note/header/footer/comment stories; no source DOCX modification',
           'rendered': False, 'factual_verification': 'See REFERENCES-REVIEW.md; report claims are not runtime authority',
           'reports': receipts}
(ROOT / 'EXTRACTION-RECEIPTS.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipts, indent=2))
