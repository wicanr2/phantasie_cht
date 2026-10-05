package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"slices"
)

// 正式建置必須以 -ldflags 注入；不從目前日期或資料夾猜版號。
var releaseVersion = "unversioned"
var engineCommit = "unversioned"

func run(ctx context.Context, args []string, stdout, stderr io.Writer) (int, error) {
	flags := flag.NewFlagSet("幽靈戰士", flag.ContinueOnError)
	flags.SetOutput(stderr)
	root := flags.String("root", "", "原版來源目錄；已匯入時不需提供")
	data := flags.String("data", "", "使用者資料根；預設採平台資料目錄")
	state := flags.String("state", "", "既有存檔目錄；預設資料根下 saves")
	lang := flags.String("lang", "zh-TW", "初始語言：zh-TW、zh-CN、en、ja、ko")
	zoom := flags.Int("zoom", 1, "視窗倍率：1 或 2")
	version := flags.Bool("version", false, "顯示版號與引擎版本")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return 0, nil
		}
		return 2, err
	}
	if flags.NArg() != 0 || (*zoom != 1 && *zoom != 2) || (*lang != "en" && !slices.Contains(languages, *lang)) {
		return 2, errors.New("參數不符；請使用 -h 查看說明")
	}
	if !validVersion(releaseVersion) || !commitPattern.MatchString(engineCommit) {
		return 1, errors.New("啟動器未帶正式版號與引擎版本")
	}
	if *version {
		fmt.Fprintf(stdout, "%s\n引擎 %s\n", releaseVersion, engineCommit)
		return 0, nil
	}
	executable, err := os.Executable()
	if err != nil {
		return 1, err
	}
	executable, err = absolute(executable)
	if err != nil {
		return 1, err
	}
	base, manifest := filepath.Dir(executable), "bundle.json"
	if runtime.GOOS == "darwin" {
		base = filepath.Dir(base)
		manifest = "Resources/bundle.json"
	}
	b, err := readBundle(base, manifest, releaseVersion, engineCommit)
	if err != nil {
		return 1, err
	}
	if runtime.GOOS != "windows" {
		info, err := os.Stat(filepath.Join(base, filepath.FromSlash(b.Backend)))
		if err != nil || info.Mode().Perm()&0o111 == 0 {
			return 1, errors.New("封包前端沒有執行權限")
		}
	}
	if *root == "" {
		*root, err = defaultSource(runtime.GOOS, executable, os.Getenv("APPIMAGE"), base, b)
		if err != nil {
			return 1, err
		}
	}
	if *data == "" {
		home, _ := os.UserHomeDir()
		*data, err = defaultData(runtime.GOOS, os.Getenv, home)
		if err != nil {
			return 1, err
		}
	}
	records, err := originalRecords()
	if err != nil {
		return 1, err
	}
	p, err := prepare(ctx, base, *root, *data, *state, b, records)
	if err != nil {
		return 1, err
	}
	defer p.Close()
	log, err := os.CreateTemp(p.Data, "launch-*.log")
	if err != nil {
		return 1, err
	}
	defer log.Close()
	backend := filepath.Join(base, filepath.FromSlash(b.Backend))
	backendArgs := []string{"-root", p.Root, "-state", p.State, "-text", filepath.Join(base, filepath.FromSlash(b.Text)),
		"-font", filepath.Join(base, filepath.FromSlash(b.Font)), "-bat", "WIZ.BAT", "-lang", *lang, "-zoom", fmt.Sprint(*zoom)}
	code, err := startBackend(ctx, backend, backendArgs, log, p.Locks)
	if err != nil || code != 0 {
		return 1, fmt.Errorf("前端啟動或執行失敗；日誌在 %s：%v", log.Name(), err)
	}
	return 0, nil
}

func main() {
	initConsole()
	ctx, stop := signal.NotifyContext(context.Background(), terminationSignals()...)
	defer stop()
	code, err := run(ctx, os.Args[1:], os.Stdout, os.Stderr)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		showError(err.Error())
	}
	os.Exit(code)
}
