// 原生啟動器契約見 docs/spec/013 §6。此 module 不連結 GUI 或 DOS 核心。
package main

import (
	"crypto/sha256"
	_ "embed"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

//go:embed original.tsv
var originalMetadata string

type fileRecord struct {
	Name   string `json:"name"`
	Bytes  int64  `json:"bytes"`
	SHA256 string `json:"sha256"`
}

type bundle struct {
	Schema        int          `json:"schema"`
	Version       string       `json:"version"`
	Engine        string       `json:"engine_commit"`
	Backend       string       `json:"backend"`
	Text          string       `json:"text"`
	Font          string       `json:"font"`
	LocalOriginal string       `json:"local_original,omitempty"`
	Assets        []fileRecord `json:"assets"`
}

var versionPattern = regexp.MustCompile(`^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$`)
var commitPattern = regexp.MustCompile(`^[0-9a-f]{40}$`)
var hashPattern = regexp.MustCompile(`^[0-9a-f]{64}$`)
var languages = []string{"zh-TW", "zh-CN", "ja", "ko"}

func validVersion(value string) bool {
	if !versionPattern.MatchString(value) {
		return false
	}
	_, err := time.Parse("20060102", value[len(value)-8:])
	return err == nil
}

func originalRecords() ([]fileRecord, error) {
	reader := csv.NewReader(strings.NewReader(originalMetadata))
	reader.Comma = '\t'
	reader.FieldsPerRecord = 3
	rows, err := reader.ReadAll()
	if err != nil || len(rows) != 71 || strings.Join(rows[0], "\t") != "name\tbytes\tsha256" {
		return nil, errors.New("啟動器原版清單無效")
	}
	var records []fileRecord
	for _, row := range rows[1:] {
		size, err := strconv.ParseInt(row[1], 10, 64)
		if err != nil || size < 0 || strings.ContainsAny(row[0], `/\:`) {
			return nil, errors.New("啟動器原版清單欄位無效")
		}
		records = append(records, fileRecord{row[0], size, row[2]})
	}
	if err := validateRecords(records); err != nil {
		return nil, err
	}
	sort.Slice(records, func(i, j int) bool { return records[i].Name < records[j].Name })
	return records, nil
}

func safeRelative(name string) bool {
	return name != "" && !strings.ContainsAny(name, `\:`) && !strings.ContainsRune(name, 0) &&
		!strings.HasPrefix(name, "/") && name != "." && filepath.ToSlash(filepath.Clean(filepath.FromSlash(name))) == name &&
		name != ".." && !strings.HasPrefix(name, "../")
}

func validateRecords(records []fileRecord) error {
	seen := map[string]bool{}
	for _, r := range records {
		key := strings.ToLower(r.Name)
		if !safeRelative(r.Name) || r.Bytes < 0 || !hashPattern.MatchString(r.SHA256) || seen[key] {
			return errors.New("檔案清單含無效路徑、大小、雜湊或重複名稱")
		}
		seen[key] = true
	}
	return nil
}

func decodeJSON(path string, value any) error {
	if err := noLinks(path); err != nil {
		return err
	}
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() {
		return errors.New("清冊須為一般檔案")
	}
	decoder := json.NewDecoder(io.LimitReader(f, 1024*1024))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(value); err != nil {
		return err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return errors.New("清冊有額外內容")
	}
	return nil
}

func verifyFile(base string, r fileRecord) error {
	path := filepath.Join(base, filepath.FromSlash(r.Name))
	if err := noLinks(path); err != nil {
		return err
	}
	f, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("必要檔案缺席或不可讀：%s：%w", path, err)
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() != r.Bytes {
		return fmt.Errorf("檔案型態或大小不符：%s", path)
	}
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return err
	}
	if hex.EncodeToString(h.Sum(nil)) != r.SHA256 {
		return fmt.Errorf("檔案版本或內容不符：%s", path)
	}
	return nil
}

func verifyFiles(base string, records []fileRecord) error {
	if err := noLinks(base); err != nil {
		return err
	}
	info, err := os.Stat(base)
	if err != nil || !info.IsDir() {
		return fmt.Errorf("找不到資料目錄：%s", base)
	}
	for _, r := range records {
		if err := verifyFile(base, r); err != nil {
			return err
		}
	}
	return nil
}

func readBundle(base, manifestName, version, engine string) (bundle, error) {
	var b bundle
	manifest := filepath.Join(base, filepath.FromSlash(manifestName))
	if err := decodeJSON(manifest, &b); err != nil {
		return b, fmt.Errorf("封包清冊不可讀：%w", err)
	}
	if b.Schema != 1 || b.Version != version || b.Engine != engine || !validVersion(version) || !commitPattern.MatchString(engine) {
		return b, errors.New("封包版號、引擎或清冊版本不符")
	}
	for _, path := range []string{b.Backend, b.Text, b.Font} {
		if !safeRelative(path) {
			return b, errors.New("封包路徑無效")
		}
	}
	if b.LocalOriginal != "" && !safeRelative(b.LocalOriginal) {
		return b, errors.New("本機原版路徑無效")
	}
	if err := validateRecords(b.Assets); err != nil {
		return b, err
	}
	assets := map[string]bool{}
	for _, r := range b.Assets {
		assets[r.Name] = true
	}
	needed := []string{b.Backend, b.Text + "/protected.tsv"}
	for _, lang := range languages {
		needed = append(needed, b.Font+"/"+lang+".golemfnt")
		for _, family := range []string{"ui", "prose", "manual"} {
			needed = append(needed, b.Text+"/"+family+"."+lang+".tsv")
		}
	}
	for _, name := range needed {
		if !assets[name] {
			return b, fmt.Errorf("封包清單缺必要檔案：%s", name)
		}
	}
	if err := verifyFiles(base, b.Assets); err != nil {
		return b, err
	}
	return b, nil
}
