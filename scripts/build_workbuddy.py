#!/usr/bin/env python3
"""Build a WorkBuddy ZIP with marketplace metadata, preserving the Codex entrypoint."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def build(output):
    root = Path(__file__).resolve().parents[1]
    metadata = json.loads((root / 'packaging/workbuddy.json').read_text(encoding='utf-8'))
    required = ('version', 'display_name', 'display_name_en', 'description_zh', 'description_en', 'author')
    for key in required:
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError('Missing WorkBuddy field: ' + key)
    skill = (root / 'SKILL.md').read_text(encoding='utf-8')
    if not skill.startswith('---\n') or '\n---\n' not in skill[4:]:
        raise ValueError('Invalid SKILL.md frontmatter')
    front, body = skill[4:].split('\n---\n', 1)
    additions = '\n'.join(key + ': ' + json.dumps(value, ensure_ascii=False)
                          for key, value in metadata.items())
    adapted = '---\n' + front + '\n' + additions + '\n---\n' + body
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = [p for p in root.rglob('*') if p.is_file() and not p.is_symlink()
             and not any(part in ('.git', '__pycache__', 'dist') for part in p.relative_to(root).parts)
             and p.suffix not in ('.pyc', '.zip') and p.name != '.DS_Store' and p.resolve() != output]
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for p in sorted(paths):
            relative = p.relative_to(root)
            content = p.read_bytes()
            if relative.as_posix() == 'SKILL.md':
                content = adapted.encode('utf-8')
            elif relative.as_posix() == 'README.md':
                content = ('# WorkBuddy 兼容包 1.0.1\n\n'
                           '此ZIP用于WorkBuddy导入，SKILL.md已包含中英文名称、描述、版本和作者。'
                           '请在WorkBuddy界面上传本包；下方install.py仅用于Codex，不要用它安装到WorkBuddy。\n\n'
                           '已做本地结构与字段校验，尚未在WorkBuddy服务端验证导入或市场审核。\n\n'
                           + content.decode('utf-8')).encode('utf-8')
            archive.writestr((Path(root.name) / relative).as_posix(), content)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output))
