//go:build linux || darwin

package main

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"syscall"
	"time"

	"golang.org/x/sys/unix"
)

func linkCount(path string) (uint64, error) {
	var info unix.Stat_t
	err := unix.Lstat(path, &info)
	return uint64(info.Nlink), err
}

func acquireLock(path string) (*os.File, error) {
	if err := noLinks(path); err != nil {
		return nil, err
	}
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE, 0o600)
	if err != nil {
		return nil, err
	}
	if info, err := f.Stat(); err != nil || !info.Mode().IsRegular() {
		f.Close()
		return nil, fmt.Errorf("鎖須為一般檔案：%s", path)
	}
	if err := unix.Flock(int(f.Fd()), unix.LOCK_EX|unix.LOCK_NB); err != nil {
		f.Close()
		return nil, fmt.Errorf("此資料或存檔已有遊戲使用：%w", err)
	}
	return f, nil
}

func startBackend(ctx context.Context, path string, args []string, log *os.File, locks []*os.File) (int, error) {
	if err := ctx.Err(); err != nil {
		return 1, err
	}
	cmd := exec.CommandContext(ctx, path, args...)
	cmd.Dir = filepath.Dir(path)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, log, log
	// flock 以開啟檔案描述綁定。子程序保留同一描述，父程序異常結束
	// 時，仍存活的前端繼續持有鎖，避免另一個實例使用同一存檔。
	cmd.ExtraFiles = locks
	if err := cmd.Run(); err != nil {
		return 1, err
	}
	return 0, nil
}

func initConsole()                    {}
func terminationSignals() []os.Signal { return []os.Signal{os.Interrupt, syscall.SIGTERM} }
func showError(message string) {
	if runtime.GOOS != "darwin" {
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	// 以 argv 傳訊息，不插入 AppleScript 語句。
	_ = exec.CommandContext(ctx, "/usr/bin/osascript", "-e",
		`on run argv
display alert "幽靈戰士" message (item 1 of argv) as critical
end run`, "--", message).Run()
}
