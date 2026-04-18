import requests
url = "https://www.idx.co.id/StaticData/NewsAndAnnouncement/ANNOUNCEMENTSTOCK/From_EREP/202204/20260418163129-61276-0/FinancialStatement-2022-III-SKYB.pdf"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
try:
    resp = requests.get(url, headers=headers)
    print("requests status:", resp.status_code)
except Exception as e:
    print("requests error:", e)
