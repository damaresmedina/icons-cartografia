import sys

with open('linhas_decisorias_stf.html', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Read the new RAW block from the user's provided file
with open('new_init.txt', 'r', encoding='utf-8') as f:
    new_block = f.read()

# Replace lines 845-944 (0-indexed) = lines 846-945 (1-indexed)
new_lines = lines[:845] + [new_block] + lines[945:]

with open('linhas_decisorias_stf.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Done. {len(lines)} -> {len(new_lines)} lines")
