package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"testing"
	"time"
)

// 只由本測試的子程序啟用，不存在於正式 executable。
func TestBackendHelper(t *testing.T) {
	if os.Getenv("PHANTASIE_TEST_BACKEND") != "1" {
		return
	}
	index := slices.Index(os.Args, "--")
	if index < 0 || index+1 >= len(os.Args) {
		os.Exit(3)
	}
	args := os.Args[index+1:]
	switch args[0] {
	case "argv":
		_ = json.NewEncoder(os.Stdout).Encode(args[1:])
		os.Exit(0)
	case "child-lease":
		fmt.Fprintf(os.Stdout, "READY %d\n", os.Getpid())
		time.Sleep(8 * time.Second)
		os.Exit(0)
	case "parent-lease":
		var locks []*os.File
		for _, name := range []string{"data.lock", "state.lock"} {
			file, err := acquireLock(filepath.Join(args[1], name))
			if err != nil {
				os.Exit(4)
			}
			locks = append(locks, file)
		}
		executable, err := os.Executable()
		if err != nil {
			os.Exit(5)
		}
		code, err := startBackend(context.Background(), executable, []string{"-test.run=^TestBackendHelper$", "--", "child-lease"}, os.Stdout, locks)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(6)
		}
		os.Exit(code)
	default:
		os.Exit(7)
	}
}

func TestBackendPreservesUnicodeAndSpaceArguments(t *testing.T) {
	t.Setenv("PHANTASIE_TEST_BACKEND", "1")
	executable, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	log, err := os.CreateTemp(t.TempDir(), "backend-*.log")
	if err != nil {
		t.Fatal(err)
	}
	defer log.Close()
	want := []string{"中文 含 空白", `literal\path`, "-root", "原版 目錄"}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	code, err := startBackend(ctx, executable, append([]string{"-test.run=^TestBackendHelper$", "--", "argv"}, want...), log, nil)
	if err != nil || code != 0 {
		t.Fatal(code, err)
	}
	if _, err := log.Seek(0, 0); err != nil {
		t.Fatal(err)
	}
	var got []string
	if err := json.NewDecoder(log).Decode(&got); err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(got, want) {
		t.Fatalf("argv changed: %q", got)
	}
}
