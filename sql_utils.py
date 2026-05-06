import re


#sql 로그 보기 좋게 하기 위한 함수
def sql_for_copy_paste(raw: object) -> str:
    s = raw.strip() if isinstance(raw, str) else str(raw).strip()

    if "SQLQuery:" in s:
        s = s.split("SQLQuery:", 1)[1].strip()

    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    start_kw = re.search(
        r"\b(WITH|SELECT|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|EXPLAIN)\b",
        s,
        re.IGNORECASE | re.DOTALL,
    )

    if start_kw:
        s = s[start_kw.start():].strip()

    s = s.replace("\\n", "\n").replace("\\t", "\t")
    return s.strip()