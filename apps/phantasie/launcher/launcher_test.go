package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"testing"
)

func writeTestFile(t *testing.T, path string, data []byte, mode os.FileMode) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, mode); err != nil {
		t.Fatal(err)
	}
}

func testRecord(name string, data []byte) fileRecord {
	h := sha256.Sum256(data)
	return fileRecord{name, int64(len(data)), hex.EncodeToString(h[:])}
}

type fixture struct {
	base, source, data, state string
	records                   []fileRecord
}

func makeFixture(t *testing.T) fixture {
	t.Helper()
	base := t.TempDir()
	// Windows 的唯讀原版副本也須能被測試框架清理。
	t.Cleanup(func() {
		_ = filepath.WalkDir(base, func(path string, entry os.DirEntry, err error) error {
			if err == nil {
				if entry.IsDir() {
					_ = os.Chmod(path, 0o700)
				} else {
					_ = os.Chmod(path, 0o600)
				}
			}
			return nil
		})
	})
	f := fixture{base: filepath.Join(base, "封包"), source: filepath.Join(base, "原版 含 空白"), data: filepath.Join(base, "資料 含 空白")}
	f.state = filepath.Join(f.data, "saves")
	if err := os.Mkdir(f.base, 0o755); err != nil {
		t.Fatal(err)
	}
	for name, data := range map[string][]byte{"A.DAT": []byte("initial-A"), "B.DAT": []byte("initial-B"), "EMPTY": nil} {
		writeTestFile(t, filepath.Join(f.source, name), data, 0o644)
		f.records = append(f.records, testRecord(name, data))
	}
	sort.Slice(f.records, func(i, j int) bool { return f.records[i].Name < f.records[j].Name })
	return f
}

func openFixture(t *testing.T, f fixture) (*plan, error) {
	t.Helper()
	return prepare(context.Background(), f.base, f.source, f.data, f.state, bundle{}, f.records)
}

func TestImportAndColdReusePreserveSaves(t *testing.T) {
	f := makeFixture(t)
	p, err := openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	if err := verifyFiles(p.Root, f.records); err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, filepath.Join(p.State, "B.DAT"), []byte("saved-progress"), 0o600)
	p.Close()
	// 已匯入時外部來源可以消失，讀回仍用同一份原版及存檔。
	if err := os.Rename(f.source, f.source+"-away"); err != nil {
		t.Fatal(err)
	}
	p, err = openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	defer p.Close()
	value, err := os.ReadFile(filepath.Join(p.State, "B.DAT"))
	if err != nil || string(value) != "saved-progress" {
		t.Fatalf("save overwritten: %q %v", value, err)
	}
	value, err = os.ReadFile(filepath.Join(p.Root, "B.DAT"))
	if err != nil || string(value) != "initial-B" {
		t.Fatalf("root changed: %q %v", value, err)
	}
}

func TestExistingImportIgnoresChangedExternalSource(t *testing.T) {
	f := makeFixture(t)
	p, err := openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	p.Close()
	writeTestFile(t, filepath.Join(f.source, "A.DAT"), []byte("other-version"), 0o644)
	if runtime.GOOS != "windows" {
		if err := os.Symlink("absent", filepath.Join(f.source, "unused-link")); err != nil {
			t.Fatal(err)
		}
	}
	p, err = openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	defer p.Close()
	if err := verifyFiles(p.Root, f.records); err != nil {
		t.Fatal(err)
	}
}

func TestMissingAndCorruptSourceMakeNoImport(t *testing.T) {
	for _, mode := range []string{"missing", "corrupt"} {
		t.Run(mode, func(t *testing.T) {
			f := makeFixture(t)
			if mode == "missing" {
				if err := os.Remove(filepath.Join(f.source, "A.DAT")); err != nil {
					t.Fatal(err)
				}
			} else {
				writeTestFile(t, filepath.Join(f.source, "A.DAT"), []byte("wrong"), 0o644)
			}
			if p, err := openFixture(t, f); err == nil {
				p.Close()
				t.Fatal("invalid source accepted")
			}
			if _, err := os.Stat(f.data); !os.IsNotExist(err) {
				t.Fatal("preflight created data")
			}
		})
	}
}

func TestExistingCorruptImportAndReceiptNeverReplaced(t *testing.T) {
	for _, mode := range []string{"root", "receipt"} {
		t.Run(mode, func(t *testing.T) {
			f := makeFixture(t)
			p, err := openFixture(t, f)
			if err != nil {
				t.Fatal(err)
			}
			p.Close()
			path := filepath.Join(f.data, "import.json")
			if mode == "root" {
				path = filepath.Join(f.data, "original", "A.DAT")
			}
			if err := os.Chmod(path, 0o600); err != nil {
				t.Fatal(err)
			}
			writeTestFile(t, path, []byte("keep-corrupt-evidence"), 0o600)
			if p, err := openFixture(t, f); err == nil {
				p.Close()
				t.Fatal("corrupt import accepted")
			}
			value, _ := os.ReadFile(path)
			if string(value) != "keep-corrupt-evidence" {
				t.Fatal("corrupt data replaced")
			}
		})
	}
}

func TestFlatLegacyAndOverlapRejected(t *testing.T) {
	f := makeFixture(t)
	writeTestFile(t, filepath.Join(f.data, "b.dat"), []byte("existing-old-save"), 0o600)
	if p, err := openFixture(t, f); err == nil {
		p.Close()
		t.Fatal("flat save ignored")
	} else if !strings.Contains(err.Error(), "-state") {
		t.Fatal(err)
	}
	value, _ := os.ReadFile(filepath.Join(f.data, "b.dat"))
	if string(value) != "existing-old-save" {
		t.Fatal("old save changed")
	}
	f = makeFixture(t)
	f.state = f.source
	if p, err := openFixture(t, f); err == nil {
		p.Close()
		t.Fatal("overlap accepted")
	}
}

func TestHardLinkAndSymbolicLinkRejected(t *testing.T) {
	f := makeFixture(t)
	if err := os.MkdirAll(f.state, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Link(filepath.Join(f.source, "A.DAT"), filepath.Join(f.state, "A.DAT")); err != nil {
		t.Fatal(err)
	}
	if p, err := openFixture(t, f); err == nil {
		p.Close()
		t.Fatal("hard link accepted")
	}
	if runtime.GOOS == "windows" {
		return
	} // 原生 Windows 另由 Wine 路徑測試核對，不猜系統 symlink 權限。
	f = makeFixture(t)
	old := filepath.Join(f.source, "A.DAT")
	if err := os.Rename(old, old+"-target"); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(old+"-target", old); err != nil {
		t.Fatal(err)
	}
	if p, err := openFixture(t, f); err == nil {
		p.Close()
		t.Fatal("symbolic link accepted")
	}
}

func TestDataAndSharedStateLocksReleased(t *testing.T) {
	f := makeFixture(t)
	p, err := openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	if q, err := openFixture(t, f); err == nil {
		q.Close()
		t.Fatal("duplicate data accepted")
	}
	other := f
	other.data = f.data + "-other"
	if q, err := openFixture(t, other); err == nil {
		q.Close()
		t.Fatal("duplicate state accepted")
	}
	p.Close()
	q, err := openFixture(t, other)
	if err != nil {
		t.Fatal(err)
	}
	q.Close()
}

func TestInternalAndExternalStateHardLinksRejected(t *testing.T) {
	for _, external := range []bool{false, true} {
		f := makeFixture(t)
		first := filepath.Join(f.state, "FIRST.SAV")
		writeTestFile(t, first, []byte("saved-progress"), 0o600)
		second := filepath.Join(f.state, "SECOND.SAV")
		if external {
			second = filepath.Join(filepath.Dir(f.data), "outside-save")
		}
		if err := os.Link(first, second); err != nil {
			t.Fatal(err)
		}
		if p, err := openFixture(t, f); err == nil {
			p.Close()
			t.Fatal("multiply-linked save accepted")
		}
		value, _ := os.ReadFile(first)
		if string(value) != "saved-progress" {
			t.Fatal("save changed")
		}
	}
}

func TestFailedCopyAndPreparedReceiptResume(t *testing.T) {
	f := makeFixture(t)
	if err := os.Mkdir(f.data, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(filepath.Join(f.source, "B.DAT")); err != nil {
		t.Fatal(err)
	}
	if err := importOriginal(context.Background(), f.source, f.data, f.records); err == nil {
		t.Fatal("partial source imported")
	}
	entries, _ := os.ReadDir(f.data)
	if len(entries) != 0 {
		t.Fatal("failed copy left output")
	}
	writeTestFile(t, filepath.Join(f.source, "B.DAT"), []byte("initial-B"), 0o644)
	prepared, _ := json.Marshal(importRecord{1, f.records})
	writeTestFile(t, filepath.Join(f.data, "import.json"), prepared, 0o600)
	if err := importOriginal(context.Background(), f.source, f.data, f.records); err != nil {
		t.Fatal(err)
	}
	if err := verifyFiles(filepath.Join(f.data, "original"), f.records); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	second := filepath.Join(filepath.Dir(f.data), "cancelled")
	if err := os.Mkdir(second, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := importOriginal(ctx, f.source, second, f.records); err == nil {
		t.Fatal("cancelled import accepted")
	}
	entries, _ = os.ReadDir(second)
	if len(entries) != 0 {
		t.Fatal("cancelled import left data")
	}
}

func TestReadonlySourceAndUnwritableState(t *testing.T) {
	if runtime.GOOS == "windows" {
		return
	} // Windows ACL 可寫性不能用 Unix chmod 作證。
	f := makeFixture(t)
	if err := os.Chmod(f.source, 0o555); err != nil {
		t.Fatal(err)
	}
	p, err := openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	p.Close()
	f = makeFixture(t)
	if err := os.MkdirAll(f.state, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(f.state, 0o555); err != nil {
		t.Fatal(err)
	}
	if p, err := openFixture(t, f); err == nil {
		p.Close()
		t.Fatal("unwritable state accepted")
	}
	if _, err := os.Stat(filepath.Join(f.data, "original")); !os.IsNotExist(err) {
		t.Fatal("unwritable state imported")
	}
}

func TestVersionHelpAndArgumentErrorsDoNotTouchData(t *testing.T) {
	oldVersion, oldEngine := releaseVersion, engineCommit
	releaseVersion, engineCommit = "v.1.0.0-20261005", strings.Repeat("a", 40)
	defer func() { releaseVersion, engineCommit = oldVersion, oldEngine }()
	for _, tc := range []struct {
		args []string
		code int
	}{
		{[]string{"-version"}, 0}, {[]string{"-h"}, 0}, {[]string{"-zoom", "3"}, 2}, {[]string{"-lang", "other"}, 2}, {[]string{"extra"}, 2},
	} {
		var out, errout bytes.Buffer
		code, _ := run(context.Background(), tc.args, &out, &errout)
		if code != tc.code {
			t.Fatalf("%v: exit %d", tc.args, code)
		}
		if len(tc.args) == 1 && tc.args[0] == "-version" && out.String() != "v.1.0.0-20261005\n引擎 "+strings.Repeat("a", 40)+"\n" {
			t.Fatal(out.String())
		}
	}
	for _, value := range []string{"v1.0.0-20261005", "v.1.0.0-20260230", "v.1.0.0-20261005\n"} {
		if validVersion(value) {
			t.Fatal("invalid version accepted")
		}
	}
}

func TestDefaultPathsAndOriginalMetadata(t *testing.T) {
	base := t.TempDir()
	env := func(key string) string {
		if key == "XDG_DATA_HOME" {
			return base
		}
		return ""
	}
	path, err := defaultData("linux", env, "")
	if err != nil || path != filepath.Join(base, "phantasie-cht") {
		t.Fatal(path, err)
	}
	if _, err := defaultData("linux", func(string) string { return "relative" }, base); err == nil {
		t.Fatal("relative data accepted")
	}
	app := filepath.Join(base, "幽靈戰士.app", "Contents", "MacOS", "launcher")
	source, err := defaultSource("darwin", app, "", base, bundle{})
	if err != nil || source != filepath.Join(base, "original") {
		t.Fatal(source, err)
	}
	image := filepath.Join(base, "含 空白.AppImage")
	source, err = defaultSource("linux", filepath.Join(base, "mounted", "usr", "bin", "launcher"), image, base, bundle{})
	if err != nil || source != filepath.Join(base, "original") {
		t.Fatal(source, err)
	}
	records, err := originalRecords()
	if err != nil || len(records) != 70 {
		t.Fatal(err)
	}
	var total int64
	for _, record := range records {
		total += record.Bytes
	}
	if total != 365982 {
		t.Fatal("metadata size changed")
	}
}

func TestBundleHashAndNecessaryAssetGates(t *testing.T) {
	base := t.TempDir()
	b := bundle{Schema: 1, Version: "v.1.0.0-20261005", Engine: strings.Repeat("a", 40), Backend: "backend", Text: "text", Font: "font"}
	names := []string{"backend", "text/protected.tsv"}
	for _, lang := range languages {
		names = append(names, "font/"+lang+".golemfnt")
		for _, family := range []string{"ui", "prose", "manual"} {
			names = append(names, "text/"+family+"."+lang+".tsv")
		}
	}
	for _, name := range names {
		data := []byte("fixture:" + name)
		writeTestFile(t, filepath.Join(base, filepath.FromSlash(name)), data, 0o755)
		b.Assets = append(b.Assets, testRecord(name, data))
	}
	encoded, _ := json.Marshal(b)
	writeTestFile(t, filepath.Join(base, "bundle.json"), encoded, 0o644)
	if _, err := readBundle(base, "bundle.json", b.Version, b.Engine); err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, filepath.Join(base, "font", "ko.golemfnt"), []byte("corrupt"), 0o644)
	if _, err := readBundle(base, "bundle.json", b.Version, b.Engine); err == nil {
		t.Fatal("corrupt font accepted")
	}
	b.Assets = b.Assets[:len(b.Assets)-1]
	encoded, _ = json.Marshal(b)
	writeTestFile(t, filepath.Join(base, "bundle.json"), encoded, 0o644)
	if _, err := readBundle(base, "bundle.json", b.Version, b.Engine); err == nil {
		t.Fatal("incomplete bundle accepted")
	}
	if err := validateRecords([]fileRecord{testRecord("../escape", nil)}); err == nil {
		t.Fatal("path escape accepted")
	}
}

func TestHDRequiresLocalBundleAndCompleteVerifiedGroup(t *testing.T) {
	base := t.TempDir()
	b := bundle{Schema: 1, Version: "v.1.0.0-20261005", Engine: strings.Repeat("a", 40), Backend: "backend", Text: "text", Font: "font", Art: "art"}
	names := []string{"backend", "text/protected.tsv"}
	for _, lang := range languages {
		names = append(names, "font/"+lang+".golemfnt")
		for _, family := range []string{"ui", "prose", "manual"} {
			names = append(names, "text/"+family+"."+lang+".tsv")
		}
	}
	for _, name := range names {
		data := []byte("fixture:" + name)
		writeTestFile(t, filepath.Join(base, filepath.FromSlash(name)), data, 0600)
		b.Assets = append(b.Assets, testRecord(name, data))
	}
	check := func(wantOK bool) {
		t.Helper()
		data, _ := json.Marshal(b)
		writeTestFile(t, filepath.Join(base, "bundle.json"), data, 0600)
		_, err := readBundle(base, "bundle.json", b.Version, b.Engine)
		if (err == nil) != wantOK {
			t.Fatalf("want accepted %v: %v", wantOK, err)
		}
	}
	check(false) // Patch cannot declare art.
	b.LocalOriginal = "original"
	check(false) // Both group members must appear in the necessary manifest.
	for _, name := range []string{"art/profile.json", "art/town-painted.png"} {
		data := []byte("synthetic:" + name)
		writeTestFile(t, filepath.Join(base, filepath.FromSlash(name)), data, 0600)
		b.Assets = append(b.Assets, testRecord(name, data))
	}
	check(true)
	file := filepath.Join(base, "art", "town-painted.png")
	original, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, file, bytes.Repeat([]byte{'x'}, len(original)), 0600)
	check(false) // Same size corruption must reject before starting the backend.
	writeTestFile(t, file, original, 0600)
	b.Art = "../art"
	check(false)
}
