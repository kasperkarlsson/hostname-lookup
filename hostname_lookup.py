import datetime
import html
import re
import requests
import urllib3


class Settings:
    FILENAME = "hostnames.txt"
    OUTPUT_FILE = f"hosts_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    REPORT_TEMPLATE_FILE = "resources/report_template.html"
    MAX_TITLE_LENGTH = 50


class HostResult:
    def __init__(self):
        self.status_codes = {"http": "null", "https": "null"}
        self.resp_length = {"http": "null", "https": "null"}
        self.title = {"http": "", "https": ""}


def main() -> None:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    hostnames = parse_file(Settings.FILENAME)
    lookup_hostnames(hostnames)


def lookup_hostnames(hostnames: list):
    with open(Settings.REPORT_TEMPLATE_FILE, "r") as in_file:
        report_template = in_file.read()
    with open(Settings.OUTPUT_FILE, "w") as f:
        try:
            f.write(report_template)
            len_hostnames = len(hostnames)
            title_regex = re.compile("<title>(.{0,1000})</title>", re.IGNORECASE)
            for i in range(len_hostnames):
                host = hostnames[i]
                print(f"{i+1}/{len_hostnames}", host, end="\t")
                result = HostResult()
                for protocol in ["http", "https"]:
                    try:
                        url = f"{protocol}://{host}/"
                        response = requests.get(url, timeout=0.5, verify=False)
                        result.status_codes[protocol] = str(response.status_code)
                        result.resp_length[protocol] = str(len(response.text))
                        # Extract title
                        title = title_regex.search(response.text)
                        if title:
                            title_decoded = html.unescape(title.group(1))
                            title_cut = title_decoded[:Settings.MAX_TITLE_LENGTH]
                            clean_title = title_cut\
                                .replace("\\", "\\\\")\
                                .replace("/", "\\/")\
                                .replace("'", "\\'")
                            result.title[protocol] = clean_title
                    except requests.exceptions.Timeout:
                        pass
                    except requests.exceptions.ConnectionError:
                        pass
                    except Exception as e:
                        print(f"Uncaught exception: {type(e)} - {e}")
                print(f"http:[{result.status_codes['http']} {result.resp_length['http']}]\t"
                      f"https:[{result.status_codes['https']} {result.resp_length['https']}]\t"
                      f"title:['{result.title['http']}' / '{result.title['https']}']")
                f.write("<script>results.push({"
                        f"host:'{host}',"
                        f"http_code:{result.status_codes['http']},"
                        f"http_len:{result.resp_length['http']},"
                        f"https_code:{result.status_codes['https']},"
                        f"https_len:{result.resp_length['https']},"
                        f"http_title:'{result.title['http']}',"
                        f"https_title:'{result.title['https']}'"
                        "});</script>\n")
                f.flush()
        finally:
            f.write("</body>\n"
                    "</html>")


def parse_file(filename: str) -> list:
    hostnames = []
    try:
        with open(filename, "r") as f:
            for line in f:
                # Remove comments, IP and cloudflare info
                line = line[0:line.find("#")]
                hostname = line.split("\t")[0]
                # Skip lines without hostname
                if not hostname:
                    continue
                hostnames.append(hostname)
        return hostnames
    except IOError as e:
        print("IOError", e)


if __name__ == '__main__':
    main()
