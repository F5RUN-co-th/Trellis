#!/bin/bash
# deploy.sh — Copy compiled .ex5 to MT5 Experts folder
# ก็อปไฟล์ที่ compile แล้วไปยังโฟลเดอร์ MT5

SRC="D:/workspace/Doc/T.me/R&D/Trellis/Experts/Trellis.ex5"
DEST="C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/D2FFA7C3BAACDDB0A9486309DC86D5C4/MQL5/Experts/"

if [ -f "$SRC" ]; then
    cp "$SRC" "$DEST"
    echo "✓ Deployed Trellis.ex5 to MT5 Experts folder"
else
    echo "✗ Trellis.ex5 not found — compile first (Ctrl+Shift+B)"
    exit 1
fi
