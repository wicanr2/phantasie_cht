"""乾淨來源、編譯接口及交付步驟的合成反例。所有執行均在 Docker。"""
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_files as pf
import package_finish as finish
import package_work as work
import package_stage_cases as stage_cases

VERSION = "v.1.0.0-20261005"
PROJECT = "a" * 40
ENGINE = "b" * 40


class PackageWorkCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phantasie-package-work-")
        self.addCleanup(self.tmp.cleanup); self.root = Path(self.tmp.name)
        self.job = self.root / "job"; self.job.mkdir()
        self.source = {"version": VERSION, "project_commit": PROJECT, "engine_commit": ENGINE, "archives": {}}

    def archives(self, name="fixture.txt", symlink=False):
        for repo in ("project", "engine"):
            with tarfile.open(self.job / f"{repo}.tar", "w") as archive:
                info = tarfile.TarInfo(name)
                if symlink:
                    info.type = tarfile.SYMTYPE; info.linkname = "outside"
                    archive.addfile(info)
                else:
                    data = b"Synthetic source\n"; info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))

    def build(self, platform="windows"):
        (self.job / "source-inputs.json").write_text(json.dumps(self.source))
        folder = self.job / "build" / platform; folder.mkdir(parents=True)
        suffix = ".exe" if platform == "windows" else ""
        for kind in ("launcher", "backend", "receipt"):
            name = f"{kind}-amd64{suffix}"
            data = stage_cases.PackageStageCases.header(platform, console=kind == "receipt")
            if kind == "launcher": data += f"{VERSION} {ENGINE}".encode()
            (folder / name).write_bytes(data)
            package = ("github.com/wicanr2/phantasie_cht/launcher" if kind == "launcher" else
                       "github.com/wicanr2/dosgolem/apps/phantasie/cmd/phantasie-" + ("play" if kind == "backend" else "receipt"))
            text = f"/out/{name}: go1.24.13\n\tpath\t{package}\n\tbuild\tGOARCH=amd64\n\tbuild\tGOOS={platform}\n"
            (folder / f"modules-{kind}-amd64.txt").write_text(text)
        if platform == "linux":
            (folder / "launcher-version.txt").write_text(f"{VERSION}\n引擎 {ENGINE}\n")
            (folder / "backend-dynamic.txt").write_text("".join(f"(NEEDED) Shared library: [{name}]\n" for name in ("libX11.so.6", "libm.so.6", "libc.so.6")))
            (folder / "backend-symbol-versions.txt").write_text("GLIBC_2.4 GLIBC_2.17 GLIBC_2.34\n")
        return folder

    def test_clean_exports_preserve_sources_and_existing_outputs(self):
        self.archives(); before = {p: p.read_bytes() for p in self.job.iterdir()}
        result = work.export_sources(self.job, VERSION, PROJECT, ENGINE)
        self.assertEqual((self.job / "source/project/fixture.txt").read_bytes(), b"Synthetic source\n")
        self.assertEqual(result["project_commit"], PROJECT)
        with self.assertRaisesRegex(ValueError, "已存在"): work.export_sources(self.job, VERSION, PROJECT, ENGINE)
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_export_rejects_path_escape_links_and_bad_version(self):
        for name, link in (("../escape", False), ("fixture", True)):
            self.archives(name, link)
            with self.assertRaises(ValueError): work.export_sources(self.job, VERSION, PROJECT, ENGINE)
            self.assertFalse((self.job / "source").exists())
        self.archives()
        with self.assertRaises(ValueError): work.export_sources(self.job, "v.1.0.0-20260230", PROJECT, ENGINE)
        self.assertFalse((self.job / "source").exists())

    def test_build_metadata_modules_versions_and_linux_abi(self):
        folder = self.build("linux")
        result = work.verify_build(self.job, "linux", VERSION, ENGINE)
        self.assertEqual(result["maximum_glibc_symbol"], "2.34")
        self.assertEqual(result["linux_direct_dependencies"], ["libX11.so.6", "libc.so.6", "libm.so.6"])
        self.assertEqual(len(result["binaries"]), 3)
        self.assertTrue((folder / "build-verification.json").exists())

    def test_unlisted_module_wrong_version_and_role_fail(self):
        folder = self.build(); path = folder / "modules-launcher-amd64.txt"; data = path.read_text()
        for bad in (data + "\tdep\tfixture.invalid/module\tv2.0.0\n", data.replace("/launcher\n", "/wrong\n"),
                    data.replace("/launcher\n", "/launcher-other\n"), data.replace("/launcher\n", "/launcher/unexpected\n"),
                    data.replace("GOARCH=amd64", "GOARCH=amd64-other"), data.replace("GOOS=windows", "GOOS=windows-other")):
            path.write_text(bad)
            with self.assertRaises(ValueError): work.verify_build(self.job, "windows", VERSION, ENGINE)
            self.assertFalse((folder / "build-verification.json").exists())
        path.write_text(data)
        (folder / "launcher-amd64.exe").write_bytes(stage_cases.PackageStageCases.header("windows") + b"unversioned")
        with self.assertRaisesRegex(ValueError, "啟動器未帶"): work.verify_build(self.job, "windows", VERSION, ENGINE)
        with self.assertRaisesRegex(ValueError, "乾淨來源"): work.verify_build(self.job, "windows", VERSION, "c" * 40)

    def test_cli_missing_font_choice_stops_before_git_or_docker(self):
        script = Path(work.__file__).with_name("package.sh")
        for args, expected in (([], "缺少合法完整版號"), (["all", "--version", VERSION], "字型條款未定案")):
            result = subprocess.run(["bash", str(script), *args], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(expected, result.stderr.decode())
            self.assertNotIn("docker", result.stderr.decode().lower())

    def test_container_mount_loop_preserves_package_name(self):
        script = Path(work.__file__).with_name("package.sh").read_text()
        function = script[script.index("run() {"):script.index("# 先由容器")]
        harness = 'set -eu\nname=fixture-package\njob_name=fixture-job\ncounter=0\njob=/tmp/nonexistent-fixture\nbase=()\ntimeout() { :; }\n'
        tail = '\nrun fixture-image\ntest "$counter" = 1\ntest "$name" = fixture-package\n'
        result = subprocess.run(["bash", "-c", harness + function + tail], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(function.count("  local name\n"), 1)
        old = function.replace("  local name\n", "", 1)
        result = subprocess.run(["bash", "-c", harness + old + tail], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_actual_synthetic_zip_and_delivery_manifest(self):
        fixture = stage_cases.PackageStageCases(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        job = fixture.root / "job"; job.mkdir(); (job / "stage").mkdir(); (job / "artifacts").mkdir()
        (job / "source-inputs.json").write_text(json.dumps(self.source))
        folder = job / "stage" / f"phantasie-cht-{VERSION}-windows-amd64-patch"
        fixture.binaries("windows"); fixture.prepare(output=folder)
        build = job / "build/windows"; build.mkdir(parents=True)
        binaries = {}
        for kind, path in (("launcher", fixture.launcher), ("backend", fixture.backend), ("receipt", fixture.receipt)):
            name = f"{kind}-amd64.exe"; data = path.read_bytes(); (build / name).write_bytes(data)
            binaries[name] = pf.record(name, data)
        (build / "build-verification.json").write_text(json.dumps({"version": VERSION, "engine_commit": ENGINE, "platform": "windows", "binaries": binaries}))
        archive = job / "artifacts" / (folder.name + ".zip")
        pf.make_zip(folder, archive, VERSION, "windows")
        delivery = fixture.root / "delivery"; delivery.mkdir()
        result = finish.finish(job, delivery, fixture.original, VERSION, PROJECT, ENGINE, "OFL-1.1")
        self.assertEqual(result["status"], "built and inspected; platform smoke pending")
        target = delivery / VERSION / "patch" / archive.name
        self.assertEqual(target.read_bytes(), archive.read_bytes())
        self.assertEqual(json.loads((delivery / VERSION / "SHA256SUMS.json").read_text()), result)
        with self.assertRaisesRegex(ValueError, "不得覆寫"):
            finish.finish(job, delivery, fixture.original, VERSION, PROJECT, ENGINE, "OFL-1.1")
        # 實際封裝損毀須在建立新交付前失敗；舊交付及來源保留。
        archive.write_bytes(b"WRONG ZIP")
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            finish.verify(job, fixture.original, VERSION, PROJECT, ENGINE, "OFL-1.1")
        self.assertEqual(target.stat().st_size, result["packages"][0]["bytes"])

    def test_failed_delivery_copy_removes_only_new_version(self):
        artifact = self.job / "synthetic.zip"; artifact.write_bytes(b"synthetic archive")
        (self.job / "artifacts").mkdir(); shutil.copyfile(artifact, self.job / "artifacts/synthetic.zip")
        delivery = self.root / "delivery"; delivery.mkdir(); (delivery / "keep").write_bytes(b"preserve")
        result = {"packages": [{"name": "synthetic.zip", "directory": "patch", "bytes": 17, "sha256": pf.digest(b"synthetic archive")} ]}
        original = self.root / "original"; original.mkdir()
        original_open = Path.open
        def fail_copy(path, *args, **kwargs):
            if path == delivery / VERSION / "patch/synthetic.zip": raise OSError("synthetic copy failure")
            return original_open(path, *args, **kwargs)
        with patch.object(finish, "verify", return_value=result), patch.object(Path, "open", fail_copy), self.assertRaises(OSError):
            finish.finish(self.job, delivery, original, VERSION, PROJECT, ENGINE, "OFL-1.1")
        self.assertFalse((delivery / VERSION).exists()); self.assertEqual((delivery / "keep").read_bytes(), b"preserve")
        self.assertEqual(artifact.read_bytes(), b"synthetic archive")


if __name__ == "__main__": unittest.main()
