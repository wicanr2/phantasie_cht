"""F1 Help 正式文字與清冊反例，原版不參與。"""
from pathlib import Path
import unittest
import package_text_cases as text_cases
import package_files_cases as file_cases
import package_text as pt
import package_files as pf
import package_stage_cases as stage_cases
import package_stage as ps
import tarfile
import io

KEYS = ('title', 'pause', 'open', 'close', 'language', 'theme', 'fullscreen', 'arrows', 'confirm', 'letters', 'context', 'footer')

def help_files(path, translation='TEST'):
    for lang in ('zh-TW', 'zh-CN', 'en', 'ja', 'ko'):
        (path/f'help.{lang}.tsv').write_text('key\ttranslation\tsource\n'+''.join(f'{key}\t{translation}\tHelp\n' for key in KEYS))

class HelpPackageCases(unittest.TestCase):
    def test_exact_five_help_and_no_partial_source(self):
        f=text_cases.PackageTextCases(); f.setUp(); self.addCleanup(f.doCleanups)
        help_files(f.source)
        files,_=pt.collect(f.source)
        self.assertEqual({n for n in files if n.startswith('help.')}, {f'help.{l}.tsv' for l in ('zh-TW','zh-CN','en','ja','ko')})
        (f.source/'help.ko.tsv').unlink()
        with self.assertRaisesRegex(ValueError,'五語齊全'):pt.collect(f.source)

    def test_manifest_contains_help_and_missing_glyph_fails(self):
        f=file_cases.PackageFilesCases(); f.setUp(); self.addCleanup(f.doCleanups)
        stage,base,text,font,_,_=f.fixture('windows')
        help_files(base/text)
        result=pf.bundle_data(stage,'windows',file_cases.VERSION,file_cases.ENGINE)[1]
        self.assertEqual(len(result['assets']),23)
        self.assertEqual({r['name'] for r in result['assets'] if '/help.' in r['name']}, {f'text/help.{l}.tsv' for l in ('zh-TW','zh-CN','en','ja','ko')})
        p=base/text/'help.zh-TW.tsv'
        p.write_text(p.read_text().replace('TEST','缺'))
        with self.assertRaises(ValueError):pf.bundle_data(stage,'windows',file_cases.VERSION,file_cases.ENGINE)

    def test_help_key_shape_ascii_and_width_failures(self):
        f=text_cases.PackageTextCases(); f.setUp(); self.addCleanup(f.doCleanups)
        help_files(f.source)
        p=f.source/'help.en.tsv'; original=p.read_text()
        for bad in [original.replace('title\t','unknown\t'),original.replace('pause\t','title\t'),original.replace('TEST','中文'),original.replace('TEST','A'*73),original.replace('TEST','TE\u0085ST'),original.replace('\tHelp\n','\tHel\u0085p\n')]:
            p.write_text(bad)
            with self.assertRaises(ValueError):pt.collect(f.source)

    def test_stage_rebuilds_help_only_glyph_and_includes_all_tables(self):
        f=stage_cases.PackageStageCases(); f.setUp(); self.addCleanup(f.doCleanups)
        f.binaries('windows')
        with tarfile.open(f.fixture.tar) as archive:
            members={m.name:archive.extractfile(m).read() for m in archive.getmembers()}
        newhex=f.hex+b'6587:'+b'FF'*32+b'\n'
        for name,_ in set(f.font_members.values()):
            members['unifont-17.0.05/font/precompiled/'+name]=newhex
        with tarfile.open(f.fixture.tar,'w:gz') as archive:
            for name,data in members.items():
                info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
        f.fixture.profile['unifont_sha256']=pf.digest(f.fixture.tar.read_bytes())
        f.font_members.update({lang:(name,pf.digest(newhex)) for lang,(name,_) in f.font_members.items()})
        help_files(f.text, '文')
        # 英文 Help 使用 ASCII。
        (f.text/'help.en.tsv').write_text((f.text/'help.en.tsv').read_text().replace('文','HELP'))
        f.prepare()
        bundle=pf.bundle_data(f.output,'windows','v.1.0.0-20261005','b'*40)[1]
        self.assertEqual(len(bundle['assets']),23)
        for lang in ('zh-TW','zh-CN','ja','ko'):
            data=(f.output/'font'/f'{lang}.golemfnt').read_bytes()
            import struct
            glyphs={struct.unpack_from('<I',data,o)[0]:data[o+5:o+37] for o in range(16,len(data),37)}
            self.assertEqual(glyphs[0x6587],bytes([255])*32)

if __name__=='__main__':unittest.main()
