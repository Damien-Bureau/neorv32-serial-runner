# Automated binary upload for VC709

Create Python virtual environment
```bash
python -m venv .venv
```

Enter virtual environment
```bash
./.venv_windows/Scripts/activate # on Windows
source .venv_linux/bin/activate  # on Linux
```

Install requirements
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run
```bash
python main.py
```
