"""IDAPython：種進入點、匯出盤點資料。在 idat 內執行（見 ida.sh）。

只做結構性匯出，不下語意結論。每筆資料附原始位址與反組譯文字，推論另外在
docs/re/ 以證據等級標示。任何一段失敗都記進 errors，不讓整支腳本無聲中止。
"""
import hashlib
import json
import sys
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_idp
import ida_loader
import ida_pro
import ida_segment
import ida_segregs
import ida_ua
import idautils
import idc

# 用法：export_survey.py <輸出目錄> <映像> [標籤 [進入點偏移 [種子範圍起 [種子範圍迄]]]]
# 偏移一律是映像偏移（CS=0110 的偏移），十六進位。預設是常駐映像。
OUT = sys.argv[1]
BIN = sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else "resident"

# 進入點 0110:4EE5，由 dosgolem probe -seg-log 取得（#266847 10D4:00F8 → 0110:4EE5）。
# IDA 線性位址 = 載入段 0110 * 16 + 偏移。
BASE = 0x1100
ENTRY = BASE + (int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x4EE5)
# 序言種子的掃描範圍（映像偏移）。常駐映像預設為整個程式碼區；overlay 為其程式碼段落。
SEED_LO = BASE + (int(sys.argv[5], 16) if len(sys.argv) > 5 else 0)
SEED_HI = BASE + (int(sys.argv[6], 16) if len(sys.argv) > 6 else 0xC9F0)
# DGROUP 段值：進入點的第一道指令 `mov bp, 0DAFh`（sub_5FE5）與 probe 的 DS=0DAF 一致。
DGROUP = 0x0DAF
SURVEY_JSON = "/survey.json" if LABEL == "resident" else "/survey_%s.json" % LABEL
ASM_NAME = "/phantasi.asm" if LABEL == "resident" else "/%s.asm" % LABEL

result = {"errors": []}


def guard(name, fn):
    try:
        fn()
    except Exception:
        result["errors"].append({"step": name, "trace": traceback.format_exc()})


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def disasm(ea):
    return idc.generate_disasm_line(ea, 0)


def segment_info():
    segs = []
    s = ida_segment.get_first_seg()
    while s:
        segs.append({
            "name": ida_segment.get_segm_name(s),
            "start": s.start_ea,
            "end": s.end_ea,
            "bitness": s.bitness,
        })
        s = ida_segment.get_next_seg(s.start_ea)
    return segs


def fix_bitness_and_seed():
    s = ida_segment.get_first_seg()
    result["segments_before"] = segment_info()
    if s.bitness != 0:
        s.bitness = 0
        s.update()
    result["segments_after"] = segment_info()
    # DS、SS 的預設值設成 DGROUP。不設的話 IDA 假設 DS 等於程式碼段，
    # 把 DS 相對的資料參照算進映像前段，蓋掉 main 的指令（映像偏移 0）。
    result["sreg"] = {}
    for rg in ("ds", "ss"):
        r = ida_idp.str2reg(rg)
        ok = ida_segregs.set_default_sreg_value(s, r, DGROUP)
        result["sreg"][rg] = {"reg": r, "ok": bool(ok)}
    ida_bytes.del_items(s.start_ea, ida_bytes.DELIT_SIMPLE, s.end_ea - s.start_ea)
    ok_insn = ida_ua.create_insn(ENTRY)
    ok_func = ida_funcs.add_func(ENTRY)
    result["seed"] = {"entry": ENTRY, "create_insn": ok_insn, "add_func": bool(ok_func)}
    if LABEL != "resident":
        # overlay：程式碼段落的第一個位元組也是函式（標頭只給入口，不給全部的函式表）。
        ok2 = ida_ua.create_insn(SEED_LO) and ida_funcs.add_func(SEED_LO)
        result["seed"]["code_start"] = {"ea": SEED_LO, "ok": bool(ok2)}
    ida_auto.auto_wait()


def function_list():
    fs = []
    for f in idautils.Functions():
        fn = ida_funcs.get_func(f)
        fs.append({"ea": f, "end": fn.end_ea, "name": ida_funcs.get_func_name(f)})
    return fs


def seed_prologues():
    """以 MSC 框架序言 55 8B EC / 55 89 E5 當額外種子，只掃程式碼區（DGROUP 之前）。

    進入點可達的函式先另存為 functions_entry_reach，與這一步的結果分開記帳。
    這是啟發式種子：序言位元組也可能出現在資料裡，所以只收 IDA 能建出函式的。
    """
    result["functions_entry_reach"] = function_list()
    lo, hi = SEED_LO, SEED_HI
    seg = ida_segment.get_first_seg()
    tried = ok = 0
    ea = max(seg.start_ea, lo)
    while ea < min(hi, seg.end_ea - 3):
        b = ida_bytes.get_bytes(ea, 3)
        if b in (b"\x55\x8b\xec", b"\x55\x89\xe5") and not ida_funcs.get_func(ea):
            tried += 1
            ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
            if ida_ua.create_insn(ea) and ida_funcs.add_func(ea):
                ok += 1
        ea += 1
    result["prologue_seeds"] = {"tried": tried, "added": ok}
    ida_auto.auto_wait()


def prior_heads(ea, n):
    out = []
    cur = ea
    for _ in range(n):
        cur = idc.prev_head(cur)
        if cur == idc.BADADDR:
            break
        out.append((cur, disasm(cur)))
    out.reverse()
    return out


def guess_ah(ea):
    """往前最多 8 道指令找 mov ah/ax, imm。只是啟發式，原始反組譯另存。"""
    cur = ea
    for _ in range(8):
        cur = idc.prev_head(cur)
        if cur == idc.BADADDR:
            return None
        if idc.print_insn_mnem(cur) != "mov":
            continue
        if idc.get_operand_type(cur, 1) != idc.o_imm:
            continue
        dst = idc.print_operand(cur, 0).lower()
        val = idc.get_operand_value(cur, 1)
        if dst == "ah":
            return {"at": cur, "ah": val & 0xFF}
        if dst == "ax":
            return {"at": cur, "ah": (val >> 8) & 0xFF, "al": val & 0xFF}
    return None


def scan_instructions():
    seg = ida_segment.get_first_seg()
    ints, segconsts, ports, rep_str = [], [], [], 0
    interesting_seg = {0xB800, 0xB000, 0xA000, 0xB900, 0xB400, 0xB1FF}
    for ea in idautils.Heads(seg.start_ea, seg.end_ea):
        if not ida_bytes.is_code(ida_bytes.get_flags(ea)):
            continue
        mn = idc.print_insn_mnem(ea)
        if mn == "int":
            ints.append({
                "ea": ea,
                "int": idc.get_operand_value(ea, 0),
                "func": ida_funcs.get_func_name(ea) or "",
                "ah_guess": guess_ah(ea),
                "context": [(a, t) for a, t in prior_heads(ea, 4)] + [(ea, disasm(ea))],
            })
        elif mn in ("in", "out"):
            ports.append({"ea": ea, "func": ida_funcs.get_func_name(ea) or "",
                          "context": prior_heads(ea, 3) + [(ea, disasm(ea))]})
        for n in range(2):
            if idc.get_operand_type(ea, n) == idc.o_imm and (idc.get_operand_value(ea, n) & 0xFFFF) in interesting_seg:
                segconsts.append({"ea": ea, "func": ida_funcs.get_func_name(ea) or "",
                                  "context": prior_heads(ea, 2) + [(ea, disasm(ea))]})
    result["int_sites"] = ints
    result["port_sites"] = ports
    result["video_segment_immediates"] = segconsts


def scan_strings():
    out = []
    for s in idautils.Strings():
        refs = [r for r in idautils.DataRefsTo(s.ea)]
        out.append({"ea": s.ea, "len": s.length, "text": str(s), "xrefs": refs[:8], "nxrefs": len(refs)})
    result["strings"] = out


def list_functions():
    result["functions"] = function_list()


def call_contexts():
    """int86 包裝（image+4E60）與 overlay 載入器（image+3D0F）的呼叫脈絡。

    位址由進入點流程的反組譯得到：sub_4790 以 `push 21h; call sub_5F60` 呼叫通用中斷，
    sub_1100 以 `push 0Bh; call sub_4E0F` 呼叫載入器。
    """
    for key, target in (("int86_calls", BASE + 0x4E60), ("overlay_loader_calls", BASE + 0x3D0F)):
        rows = []
        for ref in idautils.CodeRefsTo(target, 0):
            rows.append({
                "ea": ref,
                "func": ida_funcs.get_func_name(ref) or "",
                "context": [(a, t) for a, t in prior_heads(ref, 10)] + [(ref, disasm(ref))],
            })
        result[key] = rows


def counts():
    """已解碼的指令長度、已定義資料長度與其餘（以項目大小累計，不是只數首位元組）。"""
    seg = ida_segment.get_first_seg()
    code = data = 0
    for ea in idautils.Heads(seg.start_ea, seg.end_ea):
        fl = ida_bytes.get_flags(ea)
        size = ida_bytes.get_item_size(ea)
        if ida_bytes.is_code(fl):
            code += size
        elif ida_bytes.is_data(fl):
            data += size
    total = seg.end_ea - seg.start_ea
    result["byte_classes"] = {"code": code, "data": data, "unknown": total - code - data, "total": total}


def write_json():
    with open(OUT + SURVEY_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


def main():
    result["input"] = {"path": BIN, "sha256": sha256_file(BIN)}
    ida_auto.auto_wait()
    guard("fix_bitness_and_seed", fix_bitness_and_seed)
    guard("seed_prologues", seed_prologues)
    guard("list_functions", list_functions)
    guard("call_contexts", call_contexts)
    guard("counts", counts)
    guard("scan_instructions", scan_instructions)
    guard("scan_strings", scan_strings)
    result["function_count"] = len(result.get("functions", []))
    write_json()

    def gen_asm():
        seg = ida_segment.get_first_seg()
        r = idc.gen_file(idc.OFILE_ASM, OUT + ASM_NAME, seg.start_ea, seg.end_ea, 0)
        result["gen_asm_return"] = r

    guard("gen_asm", gen_asm)

    def save_db():
        ida_loader.save_database(ida_loader.get_path(ida_loader.PATH_TYPE_IDB), 0)

    guard("save_db", save_db)
    write_json()
    ida_pro.qexit(0)


main()
