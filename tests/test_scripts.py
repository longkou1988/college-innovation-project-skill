import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile
ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/(name+'.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
reader, installer = module('inspect_office'), module('install')
class Tests(unittest.TestCase):
    def test_docx_order_table_content_control(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'sample.docx'
            with ZipFile(p,'w') as z:
                z.writestr('word/document.xml','''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>标题</w:t><w:tab/><w:t>测试</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr><w:p><w:r><w:t>预算（元）</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:sdt><w:sdtContent><w:p><w:r><w:t>审批区</w:t></w:r></w:p></w:sdtContent></w:sdt></w:body></w:document>''')
            before=p.read_bytes(); out=reader.inspect(p)['blocks']
            self.assertEqual(out[0]['text'],'标题\t测试')
            self.assertEqual(out[1]['rows'][0][0]['grid_span']['val'],'2')
            self.assertEqual(out[1]['rows'][0][0]['blocks'][0]['text'],'预算（元）')
            self.assertEqual(out[2]['text'],'审批区')
            self.assertEqual(p.read_bytes(),before)
    def test_xlsx_strings_formula_hidden_merges(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'sample.xlsx'
            with ZipFile(p,'w') as z:
                z.writestr('xl/workbook.xml','''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="信息表" state="hidden" r:id="rId1"/></sheets></workbook>''')
                z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                z.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><r><t>项目</t></r><r><t>名称</t></r></si></sst>')
                z.writestr('xl/worksheets/sheet1.xml','''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1" hidden="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>小计</t></is></c><c r="C1"><f>SUM(C2:C8)</f></c></row></sheetData><mergeCells><mergeCell ref="A1:A2"/></mergeCells></worksheet>''')
            before=p.read_bytes(); out=reader.inspect(p)['sheets'][0]
            self.assertEqual([c['value'] for c in out['cells']],['项目名称','小计',None])
            self.assertTrue(out['cells'][2]['has_formula'])
            self.assertEqual(out['cells'][2]['formula'],'SUM(C2:C8)')
            self.assertEqual(out['state'],'hidden')
            self.assertEqual(out['rows'][0]['hidden'],'1')
            self.assertEqual(out['merged_cells'],['A1:A2'])
            self.assertEqual(p.read_bytes(),before)
    def test_unsupported_input(self):
        with self.assertRaisesRegex(ValueError,'Only'):
            reader.inspect('sample.pdf')
    def test_cli_error_preserves_output(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'broken.docx';p.write_text('bad')
            out=Path(td)/'keep.json';out.write_text('keep')
            r=subprocess.run([sys.executable,str(ROOT/'scripts/inspect_office.py'),str(p),'--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Cannot inspect file',r.stderr)
            self.assertEqual(out.read_text(),'keep')
    def test_install_preserves_existing(self):
        with tempfile.TemporaryDirectory() as td:
            target=installer.install(ROOT,td)
            self.assertEqual((target/'SKILL.md').read_bytes(),(ROOT/'SKILL.md').read_bytes())
            self.assertTrue((target/'references/workflow.md').is_file())
            keep=target/'local-change.txt';keep.write_text('preserve')
            with self.assertRaises(FileExistsError): installer.install(ROOT,td)
            self.assertEqual(keep.read_text(),'preserve')
    def test_install_excludes_git_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'source';source.mkdir()
            (source/'SKILL.md').write_text('test skill')
            (source/'.git').mkdir()
            (source/'.git/config').write_text('private local metadata')
            target=installer.install(source,Path(td)/'installed')
            self.assertTrue((target/'SKILL.md').exists())
            self.assertFalse((target/'.git').exists())
    def test_dry_run_no_write(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'absent'
            self.assertEqual(installer.install(ROOT,dest,True).name,installer.NAME)
            self.assertFalse(dest.exists())
    def test_recursive_install_rejected(self):
        with self.assertRaises(ValueError): installer.install(ROOT,ROOT/'subdirectory')
    def test_existing_symlink_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);(dest/installer.NAME).symlink_to(dest/'missing')
            with self.assertRaises(FileExistsError): installer.install(ROOT,dest)
            self.assertTrue((dest/installer.NAME).is_symlink())
if __name__=='__main__': unittest.main()
