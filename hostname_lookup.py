import requests
import urllib3


class Settings:
    FILENAME = "hostnames.txt"
    OUTPUT_FILE = "hosts.html"
    REPORT_TEMPLATE_FILE = "resources/report_template.html"


class HostResult:
    def __init__(self):
        self.status_codes = {"http": "null", "https": "null"}
        self.resp_length = {"http": "null", "https": "null"}


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
                    except requests.exceptions.Timeout:
                        pass
                    except requests.exceptions.ConnectionError:
                        pass
                    except Exception as e:
                        print(f"Uncaught exception: {type(e)} - {e}")
                print(f"http:[{result.status_codes['http']} {result.resp_length['http']}]\t"
                      f"https:[{result.status_codes['https']} {result.resp_length['https']}]")
                f.write("<script>results.push({"
                        f"host:'{host}',"
                        f"http_code:{result.status_codes['http']},"
                        f"http_len:{result.resp_length['http']},"
                        f"https_code:{result.status_codes['https']},"
                        f"https_len:{result.resp_length['https']}"
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
