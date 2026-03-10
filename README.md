# IDX Keterbukaan Informasi Downloader

## 🚀 Overview
This tool is a robust, stealthy Python script designed to automatically download attachment documents from the **IDX (Indonesia Stock Exchange)** Keterbukaan Informasi page. It features intelligent filtering, priority marking, and an automated daily schedule.

## ✨ Key Features
- **🛡️ Stealth Technology**: Uses `undetected-chromedriver` to bypass advanced anti-bot protections like Cloudflare.
- **📊 "Saham" Filter**: Automatically applies the "Saham" (Stocks) filter to ensure you only get relevant equity data.
- **⚙️ Programmable Config**: Easily filter out "trash" documents and mark priority items via `config.json`.
- **📗 Excel Tracking**: Saves all metadata to `idx_metadata.xlsx` with a priority column. It intelligently skips files you've already downloaded.
- **🏷️ Smart Naming**: Automatically renames files to `YYYYMMDD_Ticker_[HIGH]_Title.ext`.
- **⏰ Daily Scheduler**: Automatically starts with a 7-day catch-up and then stays active to fetch new filings every day at **08:00 AM**.

## 🛠️ Prerequisites
- **Python 3.10+** (Recommend using [Anaconda/Conda](https://www.anaconda.com/))
- **Google Chrome** installed on your system.
- **Local environment**: The script is configured to work with Chrome version 145 (can be adjusted in code).

## 📥 Installation

1. **Create and Activate Environment**:
   ```bash
   conda create -n vibe1 python=3.10
   conda activate vibe1
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration (`config.json`)
You can customize which files to ignore and which to highlight as high priority:

```json
{
    "exclude_keywords": [
        "laporan bulanan registrasi efek"
    ],
    "high_priority_keywords": [
        "laporan keuangan",
        "tender wajib",
        "dividen",
        "aksi korporasi"
    ]
}
```

## 🚀 Usage

Simply run the script:
```bash
python idx_downloader.py
```

- A Chrome window will open (visible mode). 
- If a Cloudflare challenge appears, you can solve it once manually.
- The script will navigate, filter for "Saham", and start processing the last 7 days of data.
- Once done, it will enter **Schedule Mode** and wait until 08:00 AM the next day.

## 📂 Output

- **`IDX_Downloads/`**: Folder containing all downloaded PDF, ZIP, and XLS files.
- **`idx_metadata.xlsx`**: Detailed Excel tracker with headers: `Date`, `Ticker Code`, `Priority`, `file title`, `file link`.

## 🛡️ Polite Crawling
To prevent being blocked, the script implements a **3-second delay** between downloads and handles pagination conservatively.
