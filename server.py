#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
製作班級學生資料清單 - 本機伺服器
提供靜態檔案與 /api/sheet_csv（代理 Google 試算表 CSV）。
執行後開啟 http://localhost:5002/
"""

import http.server
import os
import socketserver
import urllib.parse
import urllib.request

PORT = 5002
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class EnrollmentHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/sheet_csv":
            self.handle_sheet_csv(parsed.query)
            return
        super().do_GET()

    def handle_sheet_csv(self, query):
        params = urllib.parse.parse_qs(query)
        sheet_id = (params.get("sheet_id") or [""])[0].strip()
        gid = (params.get("gid") or ["0"])[0].strip() or "0"
        if not sheet_id:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("缺少 sheet_id".encode("utf-8"))
            return
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; enrollment/1.0)"}
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            urls = [
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
            ]
            csv_data = None
            last_err = None
            for url in urls:
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with opener.open(req, timeout=20) as resp:
                        csv_data = resp.read().decode("utf-8-sig")
                    break
                except Exception as e:
                    last_err = e
            if csv_data is None:
                raise last_err or RuntimeError("unable to fetch sheet")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.end_headers()
            self.wfile.write(csv_data.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"取得試算表錯誤: {e}\n請確認試算表已設為「知道連結的任何人可檢視」".encode(
                    "utf-8"
                )
            )


def main():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), EnrollmentHandler) as httpd:
        print(f"製作班級學生資料清單: http://localhost:{PORT}/")
        print("按 Ctrl+C 結束")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
