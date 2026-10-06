"""020 真實本機 HD 清冊的相容與身份破壞驗證。原版來源缺席時明示 SKIP。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_files


@unittest.skipUnless(all(os.environ.get(k) for k in (
    "PHANTASIE_ART_ORIGINAL", "PHANTASIE_ART_SCHEMA2", "PHANTASIE_ART_SCHEMA3"
)), "本機原版與兩組 HD 素材缺席，不算真實資產驗收")
class PartyArtCases(unittest.TestCase):
    def test_actual_assets_and_identity_rejection(self):
        original = Path(os.environ["PHANTASIE_ART_ORIGINAL"])
        for schema in (2, 3):
            source = Path(os.environ[f"PHANTASIE_ART_SCHEMA{schema}"])
            profile_bytes = (source / "profile.json").read_bytes()
            profile = json.loads(profile_bytes)
            self.assertEqual(profile["schema"], schema)
            names = ["profile.json", *(row["file"] for row in profile["images"])]
            expected = {name: (source / name).read_bytes() for name in names}
            with self.subTest(schema=schema, case="original identity preserved"):
                files, notice = package_files.art_files(source, original)
                self.assertEqual(files, expected)
                self.assertEqual(notice["profile_sha256"], hashlib.sha256(profile_bytes).hexdigest())
            for damage in ("profile", "image"):
                with self.subTest(schema=schema, case=damage), tempfile.TemporaryDirectory() as tmp:
                    copy = Path(tmp) / "art"
                    copy.mkdir()
                    for name in names:
                        shutil.copyfile(source / name, copy / name)
                    if damage == "profile":
                        changed = json.loads(profile_bytes)
                        changed["images"][0]["bytes"] += 1
                        (copy / "profile.json").write_text(json.dumps(changed), encoding="utf-8")
                    else:
                        image = copy / names[1]
                        changed = bytearray(image.read_bytes())
                        changed[-1] ^= 1
                        image.write_bytes(changed)
                    with self.assertRaises(ValueError):
                        package_files.art_files(copy, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
