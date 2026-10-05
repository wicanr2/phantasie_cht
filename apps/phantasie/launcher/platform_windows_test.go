//go:build windows

package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

func TestWindowsCrossDriveState(t *testing.T) {
	drive := os.Getenv("PHANTASIE_TEST_STATE_DRIVE")
	if drive == "" {
		t.Skip("須明示另一個測試磁碟機")
	}
	f := makeFixture(t)
	if !filepath.IsAbs(drive) || strings.EqualFold(filepath.VolumeName(drive), filepath.VolumeName(f.source)) {
		t.Fatal("cross-drive fixture uses one drive")
	}
	state, err := os.MkdirTemp(drive, "中文 存檔-")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(state)
	f.state = state
	p, err := openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	writeTestFile(t, filepath.Join(state, "B.DAT"), []byte("cross-drive-progress"), 0o600)
	p.Close()
	p, err = openFixture(t, f)
	if err != nil {
		t.Fatal(err)
	}
	defer p.Close()
	value, _ := os.ReadFile(filepath.Join(state, "B.DAT"))
	if string(value) != "cross-drive-progress" {
		t.Fatal("cross-drive save changed")
	}
}

func TestWindowsJobStopsBackendAfterParentDeath(t *testing.T) {
	t.Setenv("PHANTASIE_TEST_BACKEND", "1")
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, executable, "-test.run=^TestBackendHelper$", "--", "parent-lease", root)
	pipe, err := cmd.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = cmd.Process.Kill(); _ = cmd.Wait() }()
	lines := make(chan string, 1)
	go func() { line, _ := bufio.NewReader(pipe).ReadString('\n'); lines <- line }()
	var line string
	select {
	case line = <-lines:
	case <-ctx.Done():
		t.Fatal("child readiness timed out")
	}
	var pid uint32
	if n, err := fmt.Sscanf(line, "READY %d\n", &pid); err != nil || n != 1 {
		t.Fatal(line, err)
	}
	child, err := windows.OpenProcess(windows.SYNCHRONIZE|windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(child)
	if err := cmd.Process.Kill(); err != nil {
		t.Fatal(err)
	}
	_ = cmd.Wait()
	if result, err := windows.WaitForSingleObject(child, 3000); err != nil || result != windows.WAIT_OBJECT_0 {
		t.Fatal("job did not stop backend after parent death", result, err)
	}
	for _, name := range []string{"data.lock", "state.lock"} {
		lock, err := acquireLock(filepath.Join(root, name))
		if err != nil {
			t.Fatal("lease not released", err)
		}
		lock.Close()
	}
}
