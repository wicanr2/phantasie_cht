package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// 不跟隨任一既有路徑元件的符號連結；尚未建立的尾端交給後續 mkdir。
func noLinks(path string) error {
	abs, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	for current := abs; ; current = filepath.Dir(current) {
		info, err := os.Lstat(current)
		if err != nil && !os.IsNotExist(err) {
			return err
		}
		if err == nil && info.Mode()&os.ModeSymlink != 0 {
			return fmt.Errorf("路徑含符號連結：%s", current)
		}
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
	}
	return nil
}

func overlaps(a, b string) bool {
	for _, pair := range [][2]string{{a, b}, {b, a}} {
		rel, err := filepath.Rel(pair[0], pair[1])
		if err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
			return true
		}
	}
	return false
}

func absolute(path string) (string, error) {
	if path == "" {
		return "", errors.New("路徑不可為空")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return "", err
	}
	if err := noLinks(abs); err != nil {
		return "", err
	}
	return abs, nil
}

func defaultData(platform string, env func(string) string, home string) (string, error) {
	var base string
	switch platform {
	case "windows":
		base = env("LOCALAPPDATA")
	case "darwin":
		if home != "" {
			base = filepath.Join(home, "Library", "Application Support")
		}
	case "linux":
		base = env("XDG_DATA_HOME")
		if base == "" && home != "" {
			base = filepath.Join(home, ".local", "share")
		}
	default:
		return "", errors.New("不支援的平台")
	}
	if !filepath.IsAbs(base) {
		return "", errors.New("使用者資料根缺席或不是絕對路徑；請明示 -data")
	}
	return filepath.Join(base, "phantasie-cht"), nil
}

func defaultSource(platform, executable, appImage, base string, b bundle) (string, error) {
	if b.LocalOriginal != "" {
		return filepath.Join(base, filepath.FromSlash(b.LocalOriginal)), nil
	}
	outer := executable
	if platform == "linux" && appImage != "" {
		if !filepath.IsAbs(appImage) {
			return "", errors.New("AppImage 外檔位置無效")
		}
		outer = appImage
	}
	if platform == "darwin" {
		return filepath.Join(filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(executable)))), "original"), nil
	}
	return filepath.Join(filepath.Dir(outer), "original"), nil
}

func existingFiles(root string) ([]os.FileInfo, error) {
	if _, err := os.Stat(root); os.IsNotExist(err) {
		return nil, nil
	}
	var files []os.FileInfo
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.Type()&os.ModeSymlink != 0 {
			return fmt.Errorf("資料目錄含符號連結：%s", path)
		}
		if entry.IsDir() {
			return nil
		}
		// Windows 的目錄列舉未必提供檔案 ID。以路徑重新 Lstat，
		// 讓 SameFile 從實際檔案取得身分，避免把兩個零 ID 當成同檔。
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("資料目錄含特殊檔案：%s", path)
		}
		files = append(files, info)
		return nil
	})
	return files, err
}

func rejectHardLinks(state string, inputs ...string) error {
	if _, err := os.Stat(state); err == nil {
		if err := filepath.WalkDir(state, func(path string, entry fs.DirEntry, err error) error {
			if err != nil || entry.IsDir() {
				return err
			}
			count, err := linkCount(path)
			if err != nil {
				return err
			}
			if count > 1 {
				return fmt.Errorf("資料目錄含硬連結檔案：%s", path)
			}
			return nil
		}); err != nil {
			return err
		}
	}
	states, err := existingFiles(state)
	if err != nil {
		return err
	}
	for _, root := range inputs {
		files, err := existingFiles(root)
		if err != nil {
			return err
		}
		for _, a := range states {
			for _, b := range files {
				if os.SameFile(a, b) {
					return errors.New("存檔與唯讀輸入有硬連結重疊")
				}
			}
		}
	}
	return nil
}

func writable(path string) error {
	file, err := os.CreateTemp(path, ".phantasie-write-check-")
	if err != nil {
		return fmt.Errorf("目錄不可寫：%s：%w", path, err)
	}
	name := file.Name()
	if err := file.Close(); err != nil {
		os.Remove(name)
		return err
	}
	return os.Remove(name)
}
