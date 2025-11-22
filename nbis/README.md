# NBIS binaries (mindtct, bozorth3)

Place the NBIS executables here so myNIST can run auto‑match offline. Expected layout:

```
nbis/
├── mindtct            # or mindtct.exe on Windows
├── bozorth3           # or bozorth3.exe on Windows
└── bin/               # optional subdir if you prefer
```

Notes:
- Ensure the files are executable (`chmod +x nbis/mindtct nbis/bozorth3` on macOS/Linux).
- If the binaries live in `nbis/bin/`, they will also be detected.
- During PyInstaller build, the entire `nbis/` folder is included and `_MEIPASS` lookup will find them at runtime.
- These binaries are not provided here; download/compile NBIS from NIST, then drop them in this folder. Use the same architecture/OS as the target build.
