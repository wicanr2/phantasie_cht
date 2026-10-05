package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"strings"
)

type importRecord struct {
	Schema int          `json:"schema"`
	Files  []fileRecord `json:"files"`
}

func checkReceipt(data string, records []fileRecord) error {
	var record importRecord
	if err := decodeJSON(filepath.Join(data, "import.json"), &record); err != nil {
		return fmt.Errorf("匯入清冊不符：%w", err)
	}
	if record.Schema != 1 || !reflect.DeepEqual(record.Files, records) {
		return errors.New("匯入清冊版本不符")
	}
	return nil
}

func copyOriginal(ctx context.Context, source, destination string, records []fileRecord) error {
	for _, record := range records {
		if err := ctx.Err(); err != nil {
			return err
		}
		if err := noLinks(filepath.Join(source, record.Name)); err != nil {
			return err
		}
		input, err := os.Open(filepath.Join(source, record.Name))
		if err != nil {
			return err
		}
		output, err := os.OpenFile(filepath.Join(destination, record.Name), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
		if err != nil {
			input.Close()
			return err
		}
		_, copyErr := io.Copy(output, input)
		inputErr := input.Close()
		syncErr := output.Sync()
		closeErr := output.Close()
		if err := errors.Join(copyErr, inputErr, syncErr, closeErr); err != nil {
			return err
		}
		if err := os.Chmod(filepath.Join(destination, record.Name), 0o444); err != nil {
			return err
		}
	}
	return verifyFiles(destination, records)
}

func importOriginal(ctx context.Context, source, data string, records []fileRecord) error {
	root := filepath.Join(data, "original")
	if _, err := os.Lstat(root); err == nil {
		return errors.New("已有匯入目錄，不可替換")
	} else if !os.IsNotExist(err) {
		return err
	}
	tmp, err := os.MkdirTemp(data, ".import-")
	if err != nil {
		return err
	}
	defer func() {
		// Windows 的唯讀屬性會阻擋刪除。只恢復本次暫存內檔案的
		// 可寫屬性；已 rename 的正式 original 不在此路徑內。
		_ = filepath.WalkDir(tmp, func(path string, entry os.DirEntry, err error) error {
			if err == nil && !entry.IsDir() {
				_ = os.Chmod(path, 0o600)
			}
			return nil
		})
		_ = os.RemoveAll(tmp)
	}()
	if err := copyOriginal(ctx, source, tmp, records); err != nil {
		return err
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	receipt := filepath.Join(data, "import.json")
	file, err := os.OpenFile(receipt, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
	if os.IsExist(err) {
		// 上次程序可能在 original 的原子 rename 前結束。只有完全相符的
		// 清冊可重用；缺 original 不算匯入完成，仍重新核對來源與複本。
		if err := checkReceipt(data, records); err != nil {
			return err
		}
	} else if err != nil {
		return err
	} else {
		writeErr := json.NewEncoder(file).Encode(importRecord{1, records})
		syncErr := file.Sync()
		closeErr := file.Close()
		if err := errors.Join(writeErr, syncErr, closeErr); err != nil {
			os.Remove(receipt)
			return err
		}
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	// 呼叫端已持有資料鎖；新目錄在同一資料根內原子提交。
	return os.Rename(tmp, root)
}

type plan struct {
	Base, Source, Data, Root, State string
	Bundle                          bundle
	Locks                           []*os.File
}

func (p *plan) Close() {
	for i := len(p.Locks) - 1; i >= 0; i-- {
		p.Locks[i].Close()
	}
	p.Locks = nil
}

func prepare(ctx context.Context, base, source, data, state string, b bundle, records []fileRecord) (_ *plan, resultErr error) {
	p := &plan{Base: base, Bundle: b}
	defer func() {
		if resultErr != nil {
			p.Close()
		}
	}()
	var err error
	if p.Source, err = absolute(source); err != nil {
		return nil, err
	}
	if p.Data, err = absolute(data); err != nil {
		return nil, err
	}
	p.Root = filepath.Join(p.Data, "original")
	if state == "" {
		state = filepath.Join(p.Data, "saves")
	}
	if p.State, err = absolute(state); err != nil {
		return nil, err
	}
	if overlaps(p.State, p.Source) || overlaps(p.State, p.Root) || overlaps(p.State, base) || overlaps(p.Data, base) || overlaps(p.Data, p.Source) || p.State == p.Data {
		return nil, errors.New("包內資料、原版、匯入與存檔目錄不得重疊")
	}
	// 舊前端平面存檔不能默默視為空資料根。
	entries, readErr := os.ReadDir(p.Data)
	if readErr != nil && !os.IsNotExist(readErr) {
		return nil, readErr
	}
	legacyNames := map[string]bool{}
	for _, r := range records {
		legacyNames[strings.ToLower(r.Name)] = true
	}
	for _, entry := range entries {
		if legacyNames[strings.ToLower(entry.Name())] {
			return nil, errors.New("資料根有舊存檔；請改用另一個 -data，並以 -state 指向原存檔目錄")
		}
	}
	activeInputs := []string{p.Root, base}
	if _, err := os.Lstat(p.Root); os.IsNotExist(err) {
		activeInputs = append(activeInputs, p.Source)
		if err := verifyFiles(p.Source, records); err != nil {
			return nil, fmt.Errorf("請將支援版本的原版放在 %s，或明示 -root：%w", p.Source, err)
		}
	} else if err != nil {
		return nil, err
	} else {
		if err := checkReceipt(p.Data, records); err != nil {
			return nil, err
		}
		if err := verifyFiles(p.Root, records); err != nil {
			return nil, err
		}
	}
	if err := rejectHardLinks(p.State, activeInputs...); err != nil {
		return nil, err
	}
	dataInputs := []string{base}
	if len(activeInputs) == 3 {
		dataInputs = append(dataInputs, p.Source)
	}
	if err := rejectHardLinks(p.Data, dataInputs...); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(p.Data, 0o755); err != nil {
		return nil, err
	}
	if err := writable(p.Data); err != nil {
		return nil, err
	}
	dataLock, err := acquireLock(filepath.Join(p.Data, ".data.lock"))
	if err != nil {
		return nil, err
	}
	p.Locks = append(p.Locks, dataLock)
	if err := os.MkdirAll(p.State, 0o755); err != nil {
		return nil, err
	}
	if err := writable(p.State); err != nil {
		return nil, err
	}
	// 狀態鎖位於狀態目錄之外，也保護跨資料根共用的明示 -state。
	stateLock, err := acquireLock(filepath.Join(filepath.Dir(p.State), "."+filepath.Base(p.State)+".phantasie-state.lock"))
	if err != nil {
		return nil, err
	}
	p.Locks = append(p.Locks, stateLock)
	// 取得鎖後重新驗證，避免把另一個程序剛提交的原版替換掉。
	if _, err := os.Lstat(p.Root); os.IsNotExist(err) {
		if err := verifyFiles(p.Source, records); err != nil {
			return nil, err
		}
		if err := importOriginal(ctx, p.Source, p.Data, records); err != nil {
			return nil, err
		}
	} else if err != nil {
		return nil, err
	}
	if err := checkReceipt(p.Data, records); err != nil {
		return nil, err
	}
	if err := verifyFiles(p.Root, records); err != nil {
		return nil, err
	}
	return p, nil
}
