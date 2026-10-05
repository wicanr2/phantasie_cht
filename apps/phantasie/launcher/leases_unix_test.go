//go:build linux

package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"golang.org/x/sys/unix"
)

func TestBackendKeepsLeasesAfterParentDeath(t *testing.T) {
	t.Setenv("PHANTASIE_TEST_BACKEND", "1")
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, executable, "-test.run=^TestBackendHelper$", "--", "parent-lease", root)
	pipe, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer pipe.Close()
	cmd.Stdout = writer
	if err := cmd.Start(); err != nil {
		writer.Close()
		t.Fatal(err)
	}
	writer.Close()
	defer func() { _ = cmd.Process.Kill(); _ = cmd.Wait() }()
	_ = pipe.SetReadDeadline(time.Now().Add(5 * time.Second))
	line, err := bufio.NewReader(pipe).ReadString('\n')
	if err != nil {
		t.Fatal(err)
	}
	var childPID int
	if count, err := fmt.Sscanf(line, "READY %d\n", &childPID); err != nil || count != 1 {
		t.Fatal(line, err)
	}
	child, err := os.FindProcess(childPID)
	if err != nil {
		t.Fatal(err)
	}
	defer child.Kill()
	pidfd, err := unix.PidfdOpen(childPID, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer unix.Close(pidfd)
	if err := cmd.Process.Kill(); err != nil {
		t.Fatal(err)
	}
	_ = cmd.Wait()
	// 父程序已終止，但子程序仍持有兩份 lease；兩者都不能重入。
	for _, name := range []string{"data.lock", "state.lock"} {
		if file, err := acquireLock(filepath.Join(root, name)); err == nil {
			file.Close()
			t.Fatal("live backend lost lease after parent death")
		}
	}
	if err := child.Kill(); err != nil {
		t.Fatal(err)
	}
	// kill 僅表示信號送出。以 pidfd 的退出事件等待該程序終止，
	// 不把 Cmd.Wait 關閉 stdout 或一次 lock 嘗試當成退出證據。
	ready := []unix.PollFd{{Fd: int32(pidfd), Events: unix.POLLIN}}
	if n, err := unix.Poll(ready, 3000); err != nil || n != 1 || ready[0].Revents&unix.POLLIN == 0 {
		t.Fatal("child exit not observed", n, err)
	}
	for _, name := range []string{"data.lock", "state.lock"} {
		file, err := acquireLock(filepath.Join(root, name))
		if err != nil {
			t.Fatal("lease not released", err)
		}
		file.Close()
	}
}
