//go:build windows

package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"unsafe"

	"golang.org/x/sys/windows"
)

func linkCount(path string) (uint64, error) {
	if err := noLinks(path); err != nil {
		return 0, err
	}
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	var info windows.ByHandleFileInformation
	err = windows.GetFileInformationByHandle(windows.Handle(f.Fd()), &info)
	return uint64(info.NumberOfLinks), err
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
	var overlapped windows.Overlapped
	if err := windows.LockFileEx(windows.Handle(f.Fd()), windows.LOCKFILE_EXCLUSIVE_LOCK|windows.LOCKFILE_FAIL_IMMEDIATELY, 0, 1, 0, &overlapped); err != nil {
		f.Close()
		return nil, fmt.Errorf("此資料或存檔已有遊戲使用：%w", err)
	}
	return f, nil
}

func startBackend(ctx context.Context, path string, args []string, log *os.File, _ []*os.File) (int, error) {
	if err := ctx.Err(); err != nil {
		return 1, err
	}
	job, err := windows.CreateJobObject(nil, nil)
	if err != nil {
		return 1, err
	}
	defer windows.CloseHandle(job)
	limit := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limit.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
	if _, err := windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limit)), uint32(unsafe.Sizeof(limit))); err != nil {
		return 1, err
	}
	app, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return 1, err
	}
	command, err := windows.UTF16PtrFromString(windows.ComposeCommandLine(append([]string{path}, args...)))
	if err != nil {
		return 1, err
	}
	dir, err := windows.UTF16PtrFromString(filepath.Dir(path))
	if err != nil {
		return 1, err
	}
	nulName, _ := windows.UTF16PtrFromString("NUL")
	nul, err := windows.CreateFile(nulName, windows.GENERIC_READ, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		return 1, err
	}
	defer windows.CloseHandle(nul)
	process := windows.CurrentProcess()
	var input, output windows.Handle
	if err := windows.DuplicateHandle(process, nul, process, &input, 0, true, windows.DUPLICATE_SAME_ACCESS); err != nil {
		return 1, err
	}
	defer windows.CloseHandle(input)
	if err := windows.DuplicateHandle(process, windows.Handle(log.Fd()), process, &output, 0, true, windows.DUPLICATE_SAME_ACCESS); err != nil {
		return 1, err
	}
	defer windows.CloseHandle(output)
	startup := windows.StartupInfo{Flags: windows.STARTF_USESTDHANDLES, StdInput: input, StdOutput: output, StdErr: output}
	startup.Cb = uint32(unsafe.Sizeof(startup))
	var child windows.ProcessInformation
	// 先暫停建立、加入 job，才恢復。前端沒有先行執行的時間窗；
	// 父程序結束時，非繼承的 job handle 關閉並停止整個子程序樹。
	if err := windows.CreateProcess(app, command, nil, nil, true, windows.CREATE_SUSPENDED, nil, dir, &startup, &child); err != nil {
		return 1, err
	}
	defer windows.CloseHandle(child.Process)
	defer windows.CloseHandle(child.Thread)
	if err := windows.AssignProcessToJobObject(job, child.Process); err != nil {
		windows.TerminateProcess(child.Process, 1)
		return 1, err
	}
	if _, err := windows.ResumeThread(child.Thread); err != nil {
		return 1, err
	}
	done := make(chan struct{})
	defer close(done)
	go func() {
		select {
		case <-ctx.Done():
			windows.TerminateJobObject(job, 1)
		case <-done:
		}
	}()
	if _, err := windows.WaitForSingleObject(child.Process, windows.INFINITE); err != nil {
		return 1, err
	}
	var code uint32
	if err := windows.GetExitCodeProcess(child.Process, &code); err != nil {
		return 1, err
	}
	return int(code), nil
}

func initConsole() {
	_, _, _ = windows.NewLazySystemDLL("kernel32.dll").NewProc("AttachConsole").Call(uintptr(0xffffffff))
	for _, entry := range []struct {
		which  uint32
		target **os.File
		name   string
	}{
		{windows.STD_OUTPUT_HANDLE, &os.Stdout, "stdout"}, {windows.STD_ERROR_HANDLE, &os.Stderr, "stderr"},
	} {
		old := (*entry.target).Fd()
		if old != 0 && old != ^uintptr(0) {
			continue
		}
		if handle, err := windows.GetStdHandle(entry.which); err == nil && handle != 0 && handle != windows.InvalidHandle {
			*entry.target = os.NewFile(uintptr(handle), entry.name)
		}
	}
}
func terminationSignals() []os.Signal { return []os.Signal{os.Interrupt} }
func showError(message string) {
	text, _ := windows.UTF16PtrFromString(message)
	title, _ := windows.UTF16PtrFromString("幽靈戰士")
	_, _, _ = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW").Call(0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), 0x10)
}
