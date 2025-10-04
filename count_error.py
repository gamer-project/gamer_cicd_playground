from collections import Counter
import re

with open("ERROR-CPP_CPPLINT.log", "r", encoding="utf-8") as f:
    lines = f.readlines()

counter = Counter()
category_map = {}

for line in lines:
    parts = line.split(":", 2)
    if len(parts) < 3:
        continue
    message = parts[2].strip()

    # 特例處理 header guard 類訊息
    if message.startswith("#ifndef header guard has wrong style"):
        message_key = "#ifndef header guard has wrong style, please use: ...  [build/header_guard] [5]"
    elif message.startswith("#endif line should be"):
        message_key = '#endif line should be "...  [build/header_guard] [5]'
    elif message.startswith("Namespace should be terminated with \"// namespace"):
        message_key = 'Namespace should be terminated with "// namespace ... [build/namespaces] [5]'
    else:
        message_key = message

    # 擷取分類，例如 [build/header_guard]
    match = re.search(r"\[([a-z_]+/[a-z_]+)\]", message_key)
    category = match.group(1) if match else "zzz_unknown"

    counter[message_key] += 1
    category_map[message_key] = category

# 根據分類字母排序後輸出
for msg in sorted(counter.keys(), key=lambda m: (category_map[m], m)):
    print(f"{msg}: {counter[msg]}")
