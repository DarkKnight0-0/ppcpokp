# PPCPOKP

This repository contains the source code of the website:

http://ppcpokp.sysbio.org.cn/

PPCPOKP is an online knowledge platform for postoperative pulmonary complication (PPC) prediction models. The platform is designed to curate, organize, and visualize published prediction models, and provide tools for model recommendation and comparison.

## What You Can Find on the Homepage

- A brief introduction to the PPCPOKP platform and its purpose.
- Core statistics of the platform (models, downloads, publications).
- Four main functional entries:
  - Dataset: browse model data extracted from published studies.
  - Analysis: view visual statistical summaries.
  - Recommendation: select suitable models based on patient-related information.
  - Comparison: compare models with interactive filtering.
- A Recent Models section showing the latest representative models.

## Main Website Modules

- Home
- Browse
- Search
- Statistics
- Tool (Recommendation and Comparison)
- Submit
- Download
- User Guide
- About Us

## Usage

This project is expected to run with Python 3.13.11.

The overall workflow is the same on Windows, macOS, and Linux:

1. Create a virtual environment.
2. Activate the virtual environment.
3. Install all dependencies from [requirements.txt](requirements.txt).
4. Start the web application with [run_waitress.py](run_waitress.py).

The only platform-specific parts are the virtual environment activation command and, on some systems, whether the Python command is `python` or `python3`.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_waitress.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 run_waitress.py
```

If your system already maps Python 3.13.11 to `python`, you can replace `python3` with `python` on macOS or Linux as well.

After startup, open the following address in your browser:

```text
http://127.0.0.1:4344
```

## Notes

- This repository is the website source code for PPCPOKP.
- Data downloads and chart-related features are provided through the web application routes and templates in this project.
