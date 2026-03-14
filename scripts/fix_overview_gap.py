"""
갭 수정:
1. JSON 데이터 재주입 (passed_visual_inspection 추가)
2. renderOverview에 passed_visual_inspection 설명 + 테이블 컬럼 추가
3. M1_CURRENT_PROGRAM_NUMBER 설명 보완
"""
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
html_path = project_root / "data-review.html"
json_path = project_root / "dashboards" / "eda_data.json"

# 1. HTML 로드
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 2. 기존 EDA_DATA JSON 교체 (새 JSON으로)
with open(json_path, "r", encoding="utf-8") as f:
    new_json = json.dumps(json.load(f), ensure_ascii=False, separators=(",", ":"))

old_marker = "const EDA_DATA = "
start = html.find(old_marker)
json_start = start + len(old_marker)
# JSON 끝 찾기: ";\n" 패턴으로 (다음 const/var/let/function 전)
json_end = html.find(";\n", json_start)
html = html[:json_start] + new_json + html[json_end:]
print("JSON replaced")

# 3. renderOverview 업데이트: passed_visual_inspection 추가
# 3a. 메타데이터 카드에 passed_visual_inspection 추가
old_meta = """    ['Machining_Process','\\uac00\\uacf5 \\uacf5\\uc815 \\ub2e8\\uacc4','Prep \\u2192 Layer 1~3 (Up/Down) \\u2192 End. \\ucd1d 10\\ub2e8\\uacc4. \\uac01 \\ub2e8\\uacc4\\ub9c8\\ub2e4 \\uc808\\uc0ad \\uc870\\uac74\\uacfc \\uc13c\\uc11c \\ud328\\ud134\\uc774 \\ub2ec\\ub77c\\uc9d1\\ub2c8\\ub2e4.'],
  ];"""

new_meta = """    ['Machining_Process','\\uac00\\uacf5 \\uacf5\\uc815 \\ub2e8\\uacc4','Prep \\u2192 Layer 1~3 (Up/Down) \\u2192 End. \\ucd1d 10\\ub2e8\\uacc4. \\uac01 \\ub2e8\\uacc4\\ub9c8\\ub2e4 \\uc808\\uc0ad \\uc870\\uac74\\uacfc \\uc13c\\uc11c \\ud328\\ud134\\uc774 \\ub2ec\\ub77c\\uc9d1\\ub2c8\\ub2e4.'],
    ['passed_visual_inspection','\\uc721\\uc548\\uac80\\uc0ac \\ud1b5\\uacfc \\uc5ec\\ubd80','\\uac00\\uacf5 \\ud6c4 \\uc81c\\ud488\\uc758 \\uc678\\uad00\\uc744 \\uc721\\uc548\\uc73c\\ub85c \\uac80\\uc0ac\\ud55c \\uacb0\\uacfc. yes=\\ud1b5\\uacfc, no=\\ubd88\\ud569\\uaca9, NaN=\\uac00\\uacf5 \\uc911\\ub2e8\\uc73c\\ub85c \\ubbf8\\uac80\\uc0ac. worn\\uc774\\uc9c0\\ub9cc \\uc721\\uc548\\uac80\\uc0ac \\ud1b5\\uacfc\\ud55c \\uc2e4\\ud5d8(#13,#14,#15,#18)\\ub3c4 \\uc788\\uc5b4 \\ud765\\ubbf8\\ub85c\\uc6b4 \\ud328\\ud134.'],
  ];"""

if old_meta in html:
    html = html.replace(old_meta, new_meta)
    print("Meta descriptions updated")
else:
    print("WARNING: meta descriptions not found for replacement")

# 3b. 테이블 헤더에 육안검사 추가
old_header = "<th>\\uac00\\uacf5 \\uc644\\ub8cc</th>"
new_header = "<th>\\uac00\\uacf5 \\uc644\\ub8cc</th><th>\\uc721\\uc548\\uac80\\uc0ac</th>"
html = html.replace(old_header, new_header)
print("Table header updated")

# 3c. 테이블 행에 육안검사 컬럼 추가
old_row = "+'<td>'+fin+'</td></tr>';"
new_row = "+'<td>'+fin+'</td><td>'+vi+'</td></tr>';"
html = html.replace(old_row, new_row)

# fin 변수 뒤에 vi 변수 추가
old_fin = """const fin=e.finalized==='yes'?'<span style="color:#22c55e">\\uc644\\ub8cc</span>':'<span style="color:#f59e0b">\\uc911\\ub2e8</span>';"""
new_fin = """const fin=e.finalized==='yes'?'<span style="color:#22c55e">\\uc644\\ub8cc</span>':'<span style="color:#f59e0b">\\uc911\\ub2e8</span>';
    const vi=e.visual_inspection==='yes'?'<span style="color:#22c55e">\\ud1b5\\uacfc</span>':(e.visual_inspection==='no'?'<span style="color:#ef4444">\\ubd88\\ud569\\uaca9</span>':'<span style="color:#888;">\\ubbf8\\uac80\\uc0ac</span>');"""
html = html.replace(old_fin, new_fin)
print("Table rows updated")

# 4. 공구 상태 설명에 육안검사 관계 추가
old_worn_desc = "\\ubd88\\ud544\\uc694\\ud55c \\uc815\\uc9c0 \\uc5c6\\uc774 \\uc801\\uc808\\ud55c \\uc2dc\\uc810\\uc5d0 \\uad50\\uccb4\\ud560 \\uc218 \\uc788\\uac8c \\ud558\\ub294 \\uac83\\uc774 \\ubaa9\\ud45c\\uc785\\ub2c8\\ub2e4."
new_worn_desc = """\\ubd88\\ud544\\uc694\\ud55c \\uc815\\uc9c0 \\uc5c6\\uc774 \\uc801\\uc808\\ud55c \\uc2dc\\uc810\\uc5d0 \\uad50\\uccb4\\ud560 \\uc218 \\uc788\\uac8c \\ud558\\ub294 \\uac83\\uc774 \\ubaa9\\ud45c\\uc785\\ub2c8\\ub2e4.';
  h+='<br><br><strong>\\uc721\\uc548\\uac80\\uc0ac(passed_visual_inspection)\\uc640\\uc758 \\uad00\\uacc4:</strong><br>';
  h+='\\uac00\\uacf5 \\ud6c4 \\uc81c\\ud488 \\uc678\\uad00\\uc744 \\uc721\\uc548\\uc73c\\ub85c \\uac80\\uc0ac\\ud55c \\uacb0\\uacfc\\uc785\\ub2c8\\ub2e4. \\ud765\\ubbf8\\ub85c\\uc6b4 \\ud328\\ud134\\uc774 \\uc788\\uc2b5\\ub2c8\\ub2e4:<br>';
  h+='\\u2022 unworn(\\uc815\\uc0c1) \\uc2e4\\ud5d8 \\u2192 \\ubaa8\\ub450 \\uc721\\uc548\\uac80\\uc0ac <strong>\\ud1b5\\uacfc</strong> (\\ub2f9\\uc5f0\\ud55c \\uacb0\\uacfc)<br>';
  h+='\\u2022 worn(\\ub9c8\\ubaa8) \\uc2e4\\ud5d8 #06~#10 \\u2192 \\uc721\\uc548\\uac80\\uc0ac <strong style="color:#ef4444">\\ubd88\\ud569\\uaca9</strong> (\\ub9c8\\ubaa8\\ub41c \\uacf5\\uad6c\\ub85c \\ud488\\uc9c8 \\ub098\\uc068)<br>';
  h+='\\u2022 worn(\\ub9c8\\ubaa8) \\uc2e4\\ud5d8 #13~#15, #18 \\u2192 \\uc721\\uc548\\uac80\\uc0ac <strong style="color:#22c55e">\\ud1b5\\uacfc</strong> (\\ub9c8\\ubaa8\\ub418\\uc5c8\\uc9c0\\ub9cc \\uc81c\\ud488\\uc740 \\uc548 OK)<br>';
  h+='\\u2022 \\uc911\\ub2e8\\ub41c \\uc2e4\\ud5d8(#04,#05,#07,#16) \\u2192 \\ubbf8\\uac80\\uc0ac (NaN)<br>';
  h+='\\uc989, <strong>\\uacf5\\uad6c\\uac00 \\ub9c8\\ubaa8\\ub418\\uc5b4\\ub3c4 \\uc81c\\ud488 \\ud488\\uc9c8\\uc740 \\uad1c\\ucc2e\\uc744 \\uc218 \\uc788\\ub2e4</strong>\\ub294 \\uc810\\uc774 \\uc911\\uc694\\ud569\\ub2c8\\ub2e4. \\ub9c8\\ubaa8 \\uac10\\uc9c0\\ub97c \\uc138\\ubd84\\ud654\\ud560 \\ub54c \\ucc38\\uace0\\ud560 \\uc218 \\uc788\\uc2b5\\ub2c8\\ub2e4."""
html = html.replace(old_worn_desc, new_worn_desc)
print("Worn description updated with visual inspection relationship")

# 5. 센서 간 관계 섹션에서 M1_CURRENT_PROGRAM_NUMBER 보완
old_axis_rel = "S\\ucd95(\\uc8fc\\ucd95)\\uc740 \\ud56d\\uc0c1 \\ud68c\\uc804 \\u2192 \\uc808\\uc0ad \\uc911 \\uc804\\ub958/\\uc804\\ub825\\uc774 \\ud575\\uc2ec"
new_axis_rel = """S\\ucd95(\\uc8fc\\ucd95)\\uc740 \\ud56d\\uc0c1 \\ud68c\\uc804 \\u2192 \\uc808\\uc0ad \\uc911 \\uc804\\ub958/\\uc804\\ub825\\uc774 \\ud575\\uc2ec';
  h+='<br><br><strong style="color:#a855f7;">\\u2463 M1 \\uadf8\\ub8f9 (\\uae30\\uacc4 \\ub808\\ubca8)</strong><br>';
  h+='M1_CURRENT_PROGRAM_NUMBER: NC \\ud504\\ub85c\\uadf8\\ub7a8 \\ubc88\\ud638 (0, 1, 4 \\uc138 \\uac00\\uc9c0 \\uac12). \\uacf5\\uc815 \\uc804\\ud658\\uc744 \\ub098\\ud0c0\\ub0c5\\ub2c8\\ub2e4.<br>';
  h+='M1_sequence_number: \\ud504\\ub85c\\uadf8\\ub7a8 \\ub0b4 \\uc2e4\\ud589 \\uc21c\\uc11c \\ubc88\\ud638.<br>';
  h+='M1_CURRENT_FEEDRATE: \\ud604\\uc7ac \\uc774\\uc1a1\\uc18d\\ub3c4. train.csv\\uc758 feedrate\\uc640 \\ub2e4\\ub97c \\uc218 \\uc788\\uc74c (\\uc2e4\\uc2dc\\uac04 \\ubcc0\\ub3d9)."""
html = html.replace(old_axis_rel, new_axis_rel)
print("M1 group description added")

# 저장
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone. File size: {len(html):,} bytes ({len(html)//1024} KB)")
