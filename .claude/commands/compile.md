# Compile Trellis EA

Compile EA และรายงานผล

## Process

### Step 1: Compile
Run MetaEditor64.exe to compile Trellis.mq5:
```bash
"D:/workspace/Doc/T.me/R&D/MetaTrader 5/MetaEditor64.exe" /compile:"D:/workspace/Doc/T.me/R&D/Trellis/Experts/Trellis.mq5" /log:"D:/workspace/Doc/T.me/R&D/Trellis/compile.log" /inc:"C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/D2FFA7C3BAACDDB0A9486309DC86D5C4/MQL5"
```

### Step 2: Read compile log
Read `compile.log` and report:
- Number of errors
- Number of warnings
- Compilation time
- List any errors with file:line references

### Step 3: Report result
```
✅ Compile successful: 0 errors, 0 warnings (XXX ms)
  → Trellis.ex5 ready for deployment

❌ Compile failed: N errors, M warnings
  Error 1: file.mqh(line): description
```

### Step 4: Suggest next action
- If success: "Run deploy.sh to copy .ex5 to MT5"
- If failed: Analyze errors and suggest fixes

## Output Format
```
## Compile Result
- Status: ✅ Success / ❌ Failed
- Errors: 0
- Warnings: 0
- Time: XXX ms

## Errors (if any)
| # | File | Line | Error |

## Next Step
- Deploy / Fix errors
```
