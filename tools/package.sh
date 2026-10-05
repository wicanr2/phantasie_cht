#!/usr/bin/env bash
# 013：主機僅編排 Git、Docker 及來源形態檢查；工作負載全部在 Docker。
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
die() { printf '%s\n' "$*" >&2; exit 1; }
usage() {
  printf '%s\n' 'tools/package.sh [all|linux|windows|macos] --version <完整版號> [--build-only]' \
    '正式包另需 --font-license <OFL-1.1|GPL-2.0-or-later-with-font-exception> --original <目錄> --unifont <tar.gz>' \
    '可選 --local、--engine <工作樹>、--modules <唯讀模組快取>、--runtime-dir <固定 runtime 目錄>、--runtime-source <來源 tar.gz>' \
    'build-only 只產生 workplace 研究編譯；正式包需精確 tag，完成後仍須平台冒煙。'
}
platform=all version='' font_license='' build_only=0 local=0
engine="$ROOT/workplace/dosgolem-fw"
modules=/home/anr2/go/pkg/mod
original='' unifont=''
runtime_dir="$ROOT/workplace/package-prototype/runtime-rebuilt"
runtime_source="$ROOT/workplace/package-prototype/runtime-source-r1.tar.gz"
if [[ $# -gt 0 && "$1" != -* ]]; then platform=$1; shift; fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --build-only) build_only=1; shift ;;
    --local) local=1; shift ;;
    --version|--font-license|--engine|--modules|--original|--unifont|--runtime-dir|--runtime-source)
      [[ $# -ge 2 && "$2" != --* ]] || die "缺少 $1 的值"
      case "$1" in
        --version) version=$2 ;; --font-license) font_license=$2 ;;
        --engine) engine=$2 ;; --modules) modules=$2 ;; --original) original=$2 ;;
        --unifont) unifont=$2 ;; --runtime-dir) runtime_dir=$2 ;; --runtime-source) runtime_source=$2 ;;
      esac
      shift 2 ;;
    *) die "未知參數：$1" ;;
  esac
done
[[ "$platform" == all || "$platform" == linux || "$platform" == windows || "$platform" == macos ]] || die '平台不符'
[[ "$version" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]] || die '缺少合法完整版號'
if [[ "$build_only" == 0 ]]; then
  [[ "$font_license" == OFL-1.1 || "$font_license" == GPL-2.0-or-later-with-font-exception ]] || die '字型條款未定案，請明示 --font-license；不採預設'
  [[ -d "$original" && ! -L "$original" && -f "$unifont" && ! -L "$unifont" ]] || die '原版或固定字型來源缺席'
fi
[[ -d "$ROOT/workplace/package-prototype" && -d "$engine" && -d "$modules" ]] || die '研究目錄、引擎或離線模組快取缺席'
[[ "$engine" == /* && "$modules" == /* ]] || die '引擎與模組快取須為絕對路徑'
if [[ "$build_only" == 0 ]]; then
  [[ "$original" == /* && "$unifont" == /* && "$runtime_dir" == /* && "$runtime_source" == /* ]] || die '正式輸入須為絕對路徑'
  if [[ "$platform" == all || "$platform" == linux ]]; then
    [[ -d "$runtime_dir" && -f "$runtime_dir/runtime-x86_64" && -f "$runtime_source" ]] || die '固定 runtime 或配套來源缺席'
  fi
fi
for repo in "$ROOT" "$engine"; do
  [[ -z "$(git -C "$repo" status --porcelain --untracked-files=normal)" ]] || die "工作樹未乾淨：$repo"
  [[ "$(git -C "$repo" config user.email)" == wicanr2@gmail.com ]] || die 'Git 作者信箱不符'
done
[[ "$(git -C "$engine" branch --show-current)" == phantasie-cht-overlay ]] || die '引擎不在指定分支'
project_commit=$(git -C "$ROOT" rev-parse HEAD)
engine_commit=$(git -C "$engine" rev-parse HEAD)
[[ "$engine_commit" =~ ^[0-9a-f]{40}$ && "$project_commit" =~ ^[0-9a-f]{40}$ ]] || die 'commit 不符'
remote_engine=$(git -C "$engine" ls-remote origin refs/heads/phantasie-cht-overlay)
[[ "${remote_engine%%[[:space:]]*}" == "$engine_commit" ]] || die '引擎 commit 與遠端指定分支不符'
if [[ "$build_only" == 0 ]]; then
  [[ "$(git -C "$ROOT" rev-parse --verify "refs/tags/$version^{commit}")" == "$project_commit" ]] || die '本機 tag 未精確指向 HEAD'
fi
PYTHON_IMAGE=sha256:933b46a028fd786c9c3d426ebabc237e29a15912231ea8de576e95f0e4f41a4c
GO_IMAGE=sha256:083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7
MAC_IMAGE=sha256:0f50c77c732087b104b3aadc3aecb352054aa37dee8e1d293523a66dfa02ba61
APPIMAGE_IMAGE=sha256:2b6f78b5cf3d3ce8f1a2756fe81303d469d545091c672ff1fb7923cbd6aa88af
images=("$PYTHON_IMAGE" "$GO_IMAGE")
[[ "$platform" != all && "$platform" != macos ]] || images+=("$MAC_IMAGE")
[[ "$build_only" == 1 || ( "$platform" != all && "$platform" != linux ) ]] || images+=("$APPIMAGE_IMAGE")
for image in "${images[@]}"; do docker image inspect "$image" >/dev/null || die "缺固定映像：$image"; done
job_name="package-run-$version-$platform-$$"
job="$ROOT/workplace/package-prototype/$job_name"
base=(--rm --network none --user "$(id -u):$(id -g)" --cpus 2 --pids-limit 128 --log-opt max-size=10m --log-opt max-file=3)
counter=0
run() {
  counter=$((counter + 1))
  frozen=()
  for name in source rights local-text; do
    if [[ -d "$job/$name" ]]; then frozen+=(-v "$job/$name:/work/$name:ro"); fi
  done
  for name in project.tar engine.tar source-inputs.json; do
    if [[ -f "$job/$name" ]]; then frozen+=(-v "$job/$name:/work/$name:ro"); fi
  done
  timeout 1200s docker run "${base[@]}" --memory 3g --name "phantasie-package-$job_name-$counter" "${frozen[@]}" "$@"
}
# 先由容器排他保留研究目錄，才可在主機用 git archive 寫入。
run -v "$ROOT:/project:ro" -v "$ROOT/workplace/package-prototype:/parent:rw" "$PYTHON_IMAGE" python -B -c \
  'import os,pathlib,sys; sys.path.insert(0,"/project/tools"); import package_text as p; p.version(sys.argv[2]); root=pathlib.Path("/parent"); assert root.stat().st_uid==os.getuid() and root.stat().st_gid==os.getgid(); work=root/sys.argv[1]; work.mkdir(); (work/"cache").mkdir(); (work/"build").mkdir()' "$job_name" "$version"
test -d "$job" || die '研究輸出未建立'
cleanup_failed_artifacts() {
  result=$?
  trap - EXIT
  if [[ "$result" != 0 && -d "$job/artifacts" ]]; then
    # trap 只在排他保留本次 job 後註冊，不能刪除已有研究或交付。
    run -v "$job/artifacts:/failed:rw" "$PYTHON_IMAGE" python -B -c \
      'import pathlib,shutil; root=pathlib.Path("/failed"); [(shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()) for p in root.iterdir()]' || true
  fi
  exit "$result"
}
trap cleanup_failed_artifacts EXIT
git -C "$ROOT" archive --format=tar --output="$job/project.tar" "$project_commit"
git -C "$engine" archive --format=tar --output="$job/engine.tar" "$engine_commit"
run -v "$ROOT:/project:ro" -v "$job:/work:rw" "$PYTHON_IMAGE" python -B /project/tools/package_work.py export \
  --work /work --version "$version" --project-commit "$project_commit" --engine-commit "$engine_commit"
test -d "$job/source" && test -d "$job/cache" && test -d "$job/build" || die '乾淨來源或輸出型態不符'
if [[ "$platform" == all ]]; then platforms=(linux windows macos); else platforms=("$platform"); fi
for target in "${platforms[@]}"; do
  run -v "$job/build:/build:rw" "$PYTHON_IMAGE" python -B -c 'import pathlib,sys; (pathlib.Path("/build")/sys.argv[1]).mkdir()' "$target"
  test -d "$job/build/$target" || die '平台輸出未建立'
  sdk=$GO_IMAGE; [[ "$target" != macos ]] || sdk=$MAC_IMAGE
  run -v "$job/source:/source:ro" -v "$modules:/mods:ro" -v "$job/cache:/cache:rw" -v "$job/build/$target:/out:rw" \
    "$sdk" bash /source/project/tools/package_build.sh "$target" "$version" "$engine_commit"
  run -v "$job:/work:rw" -v "$job/source:/source:ro" "$PYTHON_IMAGE" python -B /source/project/tools/package_work.py verify-build \
    --work /work --platform "$target" --version "$version" --engine-commit "$engine_commit"
done
if [[ "$build_only" == 1 ]]; then
  printf '研究編譯完成：%s\n未建立字型、交付包或 tag。\n' "$job"
  exit 0
fi
rights=(--out /work/rights --project /source/project --engine /source/engine --modules /mods --go-license "/work/build/${platforms[0]}/LICENSE-Go" --unifont /font-input/unifont.tar.gz)
mounts=(-v "$job:/work:rw" -v "$job/source:/source:ro" -v "$modules:/mods:ro" -v "$unifont:/font-input/unifont.tar.gz:ro")
if [[ "$platform" == all || "$platform" == linux ]]; then
  rights+=(--runtime /runtime --runtime-source /runtime-source/source.tar.gz)
  mounts+=(-v "$runtime_dir:/runtime:ro" -v "$runtime_source:/runtime-source/source.tar.gz:ro")
fi
run "${mounts[@]}" "$PYTHON_IMAGE" python -B /source/project/tools/package_rights.py "${rights[@]}"
run -v "$job:/work:rw" "$PYTHON_IMAGE" python -B -c 'from pathlib import Path; [(Path("/work")/n).mkdir() for n in ("stage","artifacts","extracted")]'
if [[ "$local" == 1 ]]; then
  run -v "$job:/work:rw" -v "$job/source:/source:ro" -v "$ROOT/text:/reference:ro" "$PYTHON_IMAGE" python -B /source/project/tools/package_work.py local-text \
    --project /source/project --reference /reference --out /work/local-text
fi
for target in "${platforms[@]}"; do
  variants=(patch); [[ "$local" == 0 ]] || variants+=(full-local)
  for variant in "${variants[@]}"; do
    arch=amd64; [[ "$target" != linux ]] || arch=x86_64; [[ "$target" != macos ]] || arch=universal
    name="phantasie-cht-$version-$target-$arch-$variant"
    suffix=''; [[ "$target" != windows ]] || suffix=.exe
    launcher="/work/build/$target/launcher-amd64$suffix"; backend="/work/build/$target/backend-amd64$suffix"
    extra=(); [[ "$target" != macos ]] || { launcher="/work/build/$target/launcher-universal"; backend="/work/build/$target/backend-universal"; extra+=(--receipt-arm64 /work/build/macos/receipt-arm64); }
    text_source=/source/project/text
    [[ "$variant" != full-local ]] || { text_source=/work/local-text; extra+=(--local); }
    run -v "$job:/work:rw" -v "$job/source:/source:ro" -v "$original:/original:ro" -v "$unifont:/font-input/unifont.tar.gz:ro" \
      "$PYTHON_IMAGE" python -B /source/project/tools/package_stage.py --out "/work/stage/$name" --platform "$target" \
      --version "$version" --project-commit "$project_commit" --engine-commit "$engine_commit" --font-license "$font_license" \
      --text-source "$text_source" --rights /work/rights --unifont /font-input/unifont.tar.gz --original /original \
      --launcher "$launcher" --backend "$backend" --receipt-amd64 "/work/build/$target/receipt-amd64$suffix" "${extra[@]}"
    if [[ "$target" == linux ]]; then
      test -d "$job/stage/$name" || die 'AppDir 缺席'
      run -v "$job:/work:rw" -v "$job/stage/$name:/stage:ro" -v "$runtime_dir:/runtime:ro" \
        "$APPIMAGE_IMAGE" bash /work/source/project/tools/package_appimage.sh "$name" "$version"
    else
      run -v "$job:/work:rw" -v "$job/stage:/stage:ro" "$PYTHON_IMAGE" python -B /work/source/project/tools/package_files.py zip \
        --stage "/stage/$name" --platform "$target" --version "$version" --archive "/work/artifacts/$name.zip"
    fi
  done
done
# 只建立交付根；原始壓縮檔及研究輸入仍唯讀。實際封包複製僅掛載交付根可寫。
reserve=(-v "$ROOT:/project:rw" -v "$ROOT/workplace:/project/workplace:ro")
if [[ -f "$ROOT/Phantasie (1987).zip" ]]; then reserve+=(-v "$ROOT/Phantasie (1987).zip:/project/Phantasie (1987).zip:ro"); fi
run "${reserve[@]}" "$PYTHON_IMAGE" python -B -c 'import os,pathlib; p=pathlib.Path("/project/dist-all"); p.mkdir(exist_ok=True); assert p.is_dir() and not p.is_symlink() and p.stat().st_uid==os.getuid() and p.stat().st_gid==os.getgid()'
test -d "$ROOT/dist-all" || die '交付根未建立'
run -v "$ROOT/dist-all:/delivery:rw" -v "$job:/work:ro" -v "$original:/original:ro" \
  "$PYTHON_IMAGE" python -B /work/source/project/tools/package_finish.py --work /work --delivery /delivery --original /original \
  --version "$version" --project-commit "$project_commit" --engine-commit "$engine_commit" --font-license "$font_license"
printf '封包已建立：%s/dist-all/%s\n平台冒煙仍待完成，不能視為正式驗收。\n' "$ROOT" "$version"
