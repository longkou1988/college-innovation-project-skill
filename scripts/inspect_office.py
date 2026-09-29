#!/usr/bin/env python3
"""Read DOCX/XLSX structure with the Python standard library; never edit input."""
import argparse
import json
import posixpath
import sys
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def text_of(element, tag):
    return ''.join(n.text or '' for n in element.iter(tag))


def attrs(element):
    return {} if element is None else {k.split('}')[-1]: v for k, v in element.attrib.items()}


def paragraph(p):
    pieces = []
    for n in p.iter():
        if n.tag == W + 't':
            pieces.append(n.text or '')
        elif n.tag == W + 'tab':
            pieces.append('\t')
        elif n.tag in (W + 'br', W + 'cr'):
            pieces.append('\n')
    props = p.find(W + 'pPr')
    return {'type': 'paragraph', 'text': ''.join(pieces),
            'properties_xml': ET.tostring(props, encoding='unicode') if props is not None else None}


def blocks(parent):
    result = []
    for node in parent:
        if node.tag == W + 'p':
            result.append(paragraph(node))
        elif node.tag == W + 'tbl':
            rows = []
            for ri, row in enumerate(node.findall(W + 'tr'), 1):
                cells = []
                for ci, cell in enumerate(row.findall(W + 'tc'), 1):
                    cells.append({'row': ri, 'cell': ci,
                                  'grid_span': attrs(cell.find(W+'tcPr/'+W+'gridSpan')),
                                  'vertical_merge': attrs(cell.find(W+'tcPr/'+W+'vMerge')),
                                  'blocks': blocks(cell)})
                rows.append(cells)
            result.append({'type': 'table', 'rows': rows})
        elif node.tag == W + 'sdt':
            content = node.find(W + 'sdtContent')
            if content is not None:
                result.extend(blocks(content))
    return result


def docx(z):
    root = ET.fromstring(z.read('word/document.xml'))
    body = root.find(W + 'body')
    parts = {}
    for name in z.namelist():
        if name.startswith(('word/header', 'word/footer')) and name.endswith('.xml'):
            parts[name] = blocks(ET.fromstring(z.read(name)))
    styles = []
    if 'word/styles.xml' in z.namelist():
        sr = ET.fromstring(z.read('word/styles.xml'))
        defaults = sr.find(W + 'docDefaults')
        if defaults is not None:
            styles.append({'defaults_xml': ET.tostring(defaults, encoding='unicode')})
        for st in sr.findall(W + 'style'):
            styles.append({'id': st.get(W+'styleId'), 'xml': ET.tostring(st, encoding='unicode')})
    return {'format': 'docx', 'blocks': blocks(body), 'headers_footers': parts,
            'sections': [ET.tostring(n, encoding='unicode') for n in root.iter(W+'sectPr')],
            'styles': styles,
            'limitations': ['Not a renderer; run-level formatting and layout require original-file inspection.',
                            'Cell numbers are XML cell positions, not expanded merged-grid coordinates.']}


def xlsx(z):
    names = set(z.namelist())
    shared = []
    if 'xl/sharedStrings.xml' in names:
        shared = [text_of(n, S+'t') for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(S+'si')]
    rels = {n.get('Id'): (n.get('Target'), n.get('TargetMode'))
            for n in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = []
    for sheet in wb.findall(S+'sheets/'+S+'sheet'):
        target, mode = rels[sheet.get(R+'id')]
        if mode == 'External':
            raise ValueError('External sheet relationships are not supported')
        name = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target))
        sr = ET.fromstring(z.read(name))
        rows, cells = [], []
        for row in sr.findall(S+'sheetData/'+S+'row'):
            rows.append(attrs(row))
            for c in row.findall(S+'c'):
                typ = c.get('t')
                val = c.find(S+'v')
                raw = val.text if val is not None else None
                if typ == 's':
                    value = shared[int(raw)] if raw is not None else None
                elif typ == 'inlineStr':
                    value = text_of(c, S+'t')
                else:
                    value = raw
                formula = c.find(S+'f')
                cells.append({'cell': c.get('r'), 'type': typ, 'style': c.get('s'),
                              'value': value, 'formula': formula.text if formula is not None else None,
                              'formula_attributes': attrs(formula),
                              'has_formula': formula is not None})
        sheets.append({'name': sheet.get('name'), 'state': sheet.get('state', 'visible'),
                       'part': name, 'cells': cells, 'rows': rows,
                       'columns': [attrs(n) for n in sr.findall(S+'cols/'+S+'col')],
                       'merged_cells': [n.get('ref') for n in sr.findall(S+'mergeCells/'+S+'mergeCell')],
                       'data_validations_xml': [ET.tostring(n, encoding='unicode') for n in sr.findall(S+'dataValidations')],
                       'page_setup': attrs(sr.find(S+'pageSetup'))})
    comments = {n: z.read(n).decode('utf-8') for n in names if n.startswith('xl/comments') and n.endswith('.xml')}
    return {'format': 'xlsx', 'sheets': sheets, 'comments_xml': comments,
            'defined_names': [ET.tostring(n, encoding='unicode') for n in wb.findall(S+'definedNames/'+S+'definedName')],
            'limitations': ['Does not calculate formulas. Null cached values remain unknown.',
                            'Numeric/date cells retain stored values; inspect number formats in the original file.']}


def inspect(path):
    path = Path(path)
    if path.suffix.lower() not in ('.docx', '.xlsx'):
        raise ValueError('Only .docx and .xlsx are supported; use existing PDF/OCR tools for other formats')
    with ZipFile(path) as z:
        return docx(z) if path.suffix.lower() == '.docx' else xlsx(z)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, help='New JSON file; existing files are never overwritten')
    args = parser.parse_args()
    try:
        data = json.dumps(inspect(args.input), ensure_ascii=False, indent=2)
        if args.output:
            with args.output.open('x', encoding='utf-8') as f:
                f.write(data + '\n')
        else:
            print(data)
    except (OSError, BadZipFile, ET.ParseError, KeyError, ValueError, IndexError) as exc:
        print(f'Cannot inspect file: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
