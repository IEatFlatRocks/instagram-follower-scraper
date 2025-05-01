# Instagram Niche Creator Finder

**Find small Instagram creators in a specific niche from any account’s followers.**  

This tool scrapes followers using `undetected-chromedriver` to bypass bot detection and leverages [GROQ](https://groq.com/) to identify each user's niche from their bio. Filter by follower count and niche relevance to quickly generate a list of target creators—ideal for UGC campaigns, brand outreach, or market research.

---

## 🔧 Features

- 🕵️ Scrapes followers of any **public** Instagram account  
- 🧠 Uses LLM (via GROQ API) to classify niche based on bio  
- 📉 Filters by follower count (e.g. **<10k followers**)  
- 🔎 Extracts bios and public stats  
- 🚫 Bypasses bot detection with `undetected-chromedriver`  

---

## 📦 Requirements

- **Python 3.8+**  
- `undetected-chromedriver`  
- `selenium`  
- `requests`  
- **GROQ API key**  
- **Instagram Account**  

### Install dependencies:

```bash
pip install -r requirements.txt
```

## ⚙️ Usage

1. **Set your GROQ API key** in a `.env` file:

```bash
GROQ_API_KEY=your_key_here
```

2. **Run the script** with a target Instagram username:

```bash
python main.py --username target_account --min_followers 100 --max_followers 10000 --niche "fitness"
```

### 🛠️ Arguments:
- **`--username`** → Instagram handle to pull followers from  
- **`--min_followers`** → Minimum follower count to include  
- **`--max_followers`** → Maximum follower count to include  
- **`--niche`** → Target niche keyword to match (e.g. `"fashion"`, `"fitness"`, `"tech"`)

---

## 🔍 How It Works
1. 🚀 **Launches** a stealth Chrome session using `undetected-chromedriver`.  
2. 📥 **Loads** the follower list of the specified Instagram account.  
3. 🔎 **For each follower:**  
   - Extracts **public bio** and **follower count**.  
   - Sends bio to **GROQ LLM** to predict niche.  
   - Filters out accounts not matching your criteria.  
4. 💾 **Saves** matching profiles to a `.csv` or `.json` file.  

---

## 📁 Output
Each matched creator includes:  
✅ **Username**  
✅ **Bio**  
✅ **Follower Count**  
✅ **Predicted Niche**  
✅ **Profile URL**  

📂 Output is saved as **`output.csv`** or **`output.json`** in the project folder.  

---

## ⚠️ Disclaimer
🚨 **This project is for educational and research purposes only.** By using this tool, you agree to:  

✔️ **Comply with Instagram’s Terms of Use**  
✔️ **Not scrape private accounts or misuse scraped data**  
✔️ **Take full responsibility for how you use the output**  

⚠️ Use this script **responsibly**—Instagram may **restrict access or ban IPs** for excessive scraping activity.