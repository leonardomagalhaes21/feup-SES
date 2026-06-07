#!/bin/bash
mkdir -p demo_target

echo "assert True" > demo_target/allowed.py

cat << 'EOF' > demo_target/warning.py
with open('/tmp/test.txt', 'w') as f:
    f.write('hello')
EOF

cat << 'EOF' > demo_target/blocked.py
import os
os.system('ls ' + 'foo')
EOF

echo -e "\n============================================="
echo "🟢 RUNNING GATEKEEPER ON: allowed.py (LOW SEVERITY)"
echo "============================================="
uv run gatekeeper scan --target demo_target/allowed.py

echo -e "\n============================================="
echo "🟡 RUNNING GATEKEEPER ON: warning.py (MEDIUM SEVERITY)"
echo "============================================="
uv run gatekeeper scan --target demo_target/warning.py

echo -e "\n============================================="
echo "🔴 RUNNING GATEKEEPER ON: blocked.py (HIGH SEVERITY)"
echo "============================================="
uv run gatekeeper scan --target demo_target/blocked.py
