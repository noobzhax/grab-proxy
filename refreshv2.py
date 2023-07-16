from ast import Num
from email import charset
from ftplib import parse150
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import re, os, logging
import threading
import requests
import concurrent.futures

session = requests.Session()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

LOGGER = logging.getLogger(__name__)


def getrooturl(url):
    if "raw.githubusercontent.com" in url:
        root = "github-" + url.split("/")[3]
    else:
        root = url.split("/")[2].replace("www.", "")
    return root

def gethtmljs(url, log):
    proxies = []
    if "[page]" in url:
        num = url.split("]")
        num = int(num[0].replace("[", ""))
        denum = num
        clock = 0
        while num > 0:
            newproxies = []
            clock += 1
            num -= 1
            newurl = url.replace("[page]", f"{clock}").replace(f"[{denum}]", "")
            try:
                html = gethtmljsraw(newurl)
            except:
                html = ""
            newproxies = extract(html)
            proxies.extend(newproxies)
            if len(newproxies) < 1:
                break
    else:
        html = gethtmljsraw(url)
        proxies = extract(html)
    rooturl = getrooturl(url)
    proxylist = '\n'.join([str(elem) for elem in proxies])
    with open("./proxies/raw.txt", "a") as f:
        f.write(f"{proxylist}\n")
    with open("./proxies/provider.csv", "a") as f:
        f.write(f"{rooturl};{len(proxies)}\n")
    return proxies

def gethtmljsraw(url):
    try:
        service = Service(executable_path="./chromedriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument("window-size=600,600")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        LOGGER.info(url)
        html = driver.page_source
        driver.quit()
        return html
    except WebDriverException as e:
        error_message = str(e)
        if "ERR_SSL_PROTOCOL_ERROR" in error_message:
            # Log the skipped error
            LOGGER.warning(f"Skipping URL due to SSL protocol error: {url}")
            return None
        else:
            # Log other WebDriverException errors
            LOGGER.exception(f"Failed to fetch HTML for {url}: {error_message}")
            return None

def gethtml(url, log):
    proxies = []
    if "[page]" in url:
        num = url.split("]")
        num = int(num[0].replace("[", ""))
        denum = num
        clock = 0
        while num > 0:
            newproxies = []
            if "hidemy.name" in url:
                clock += 64
            else:
                clock += 1
            num -= 1
            newurl = url.replace("[page]", f"{clock}").replace(f"[{denum}]", "")
            try:
                html = gethtmlraw(newurl)
            except:
                html = ""
            newproxies = extract(html)
            proxies.extend(newproxies)
            if len(newproxies) < 1:
                break
    else:
        html = gethtmlraw(url)
        proxies = extract(html)
    rooturl = getrooturl(url)
    proxylist = '\n'.join([str(elem) for elem in proxies])
    with open("./proxies/raw.txt", "a") as f:
        f.write(f"{proxylist}\n")
    with open("./proxies/provider.csv", "a") as f:
        f.write(f"{rooturl};{len(proxies)}\n")
    return proxies

def gethtmlraw(url):
    headers = {'User-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36'}
    response = session.get(url, headers=headers, timeout=30)
    html = response.content
    return html

def extract(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=":")
    text = text.replace("\n", ":").replace(" ", "")
    while "::" in text:
        text = text.replace("::", ":")
    proxies = proxy_pattern.findall(text)
    return proxies

def normalizer():
    with open("./proxies/provider.csv", "r") as f:
        providers = f.readlines()
    providers.sort()
    p0 = ""
    p1 = ""
    pall = ""
    for provider in providers:
        p = provider.split(";")
        if p[0] == p0:
            p1 = int(p1.replace("\n", "")) + int(p[1].replace("\n", ""))
            p1 = f"{p1}\n"
        else:
            pall = pall + f"{p0};{p1}"
            try:
                p1 = p[1]
            except:
                pass
        p0 = p[0]
    with open("./proxies/provider.csv", "w") as f:
        f.write(pall)
    with open("./README.md", "r") as f:
        readme = f.read()
    pall = pall.replace(";", "|")
    readme = readme.replace("#var-list", pall)

    with open("./proxies/raw.txt", "r") as f:
        proxies = f.readlines()
    proxies.sort()
    before = ""
    proxiesdup = ""
    all_proxies = 0
    nodups = 0
    for proxy in proxies:
        all_proxies += 1
        if proxy != before:
            proxiesdup += proxy
            nodups += 1
        before = proxy
    with open("./proxies/provider.csv", "a") as f:
        f.write(f"All: {all_proxies}, Without Duplicates: {nodups}")
    with open("./proxies/all.txt", "w") as f:
        f.write(proxiesdup)
    readme = readme.replace("#var-fetched", f"{all_proxies}").replace("#var-unique", f"{nodups}")
    with open("./README.md", "w") as f:
        f.write(readme)

def checker(proxy, log):
    url = "http://test.js0.ch/"
    try:
        resp = session.get(url, proxies=dict(http=f'socks5://{proxy}'), timeout=10)
        if resp.status_code == 200 and resp.text == "ok\n":
            with open("./proxies/working.csv", "a") as f:
                f.write(f"{proxy},socks5,{resp.elapsed.total_seconds()}\n")
        else:
            with open("./proxies/excluded.csv", "a") as f:
                f.write(f"{proxy},socks5,{resp.elapsed.total_seconds()}\n")
    except Exception as e:
        try:
            resp = session.get(url, proxies=dict(http=f'socks4://{proxy}'), timeout=10)
            if resp.status_code == 200 and resp.text == "ok\n":
                with open("./proxies/working.csv", "a") as f:
                    f.write(f"{proxy},socks4,{resp.elapsed.total_seconds()}\n")
            else:
                with open("./proxies/excluded.csv", "a") as f:
                    f.write(f"{proxy},socks4,{resp.elapsed.total_seconds()}\n")
        except:
            try:
                resp = session.get(url, proxies=dict(http=f'http://{proxy}'), timeout=10)
                if resp.status_code == 200 and resp.text == "ok\n":
                    with open("./proxies/working.csv", "a") as f:
                        f.write(f"{proxy},http,{resp.elapsed.total_seconds()}\n")
                else:
                    with open("./proxies/excluded.csv", "a") as f:
                        f.write(f"{proxy},http,{resp.elapsed.total_seconds()}\n")
            except:
                pass

def createfiles():
    with open("./proxies/http.txt", "w"):
        pass
    with open("./proxies/socks4.txt", "w"):
        pass
    with open("./proxies/socks5.txt", "w"):
        pass
    with open("./proxies/ultrafast.txt", "w"):
        pass
    with open("./proxies/fast.txt", "w"):
        pass
    with open("./proxies/slow.txt", "w"):
        pass
    with open("./proxies/ultraslow.txt", "w"):
        pass
    with open("./proxies/medium.txt", "w"):
        pass
    with open("./proxies/working.txt", "w"):
        pass

    with open("./proxies/excluded.csv", "r") as f:
        excludedproxies = f.readlines()
        nexcluded = len(excludedproxies)

    with open("./proxies/misconfigured.csv", "r") as f:
        misconfiguredproxies = f.readlines()
        nmisconfigured = len(misconfiguredproxies)

    with open("./proxies/working.csv", "r") as f:
        working = f.readlines()
        nhttp = 0
        nsocks4 = 0
        nsocks5 = 0
        all_proxies = 0
        nultrafast = 0
        nfast = 0
        nmedium = 0
        nslow = 0
        nultraslow = 0
        for w in working:
            all_proxies += 1
            proxy = w.rstrip().split(",")
            with open("./proxies/working.txt", "a") as f:
                f.write(f"{proxy[0]}\n")
            if proxy[1] == "http":
                nhttp += 1
                with open("./proxies/http.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif proxy[1] == "socks4":
                nsocks4 += 1
                with open("./proxies/socks4.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif proxy[1] == "socks5":
                nsocks5 += 1
                with open("./proxies/socks5.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            if float(proxy[2]) < 0.5:
                nultrafast += 1
                with open("./proxies/ultrafast.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif float(proxy[2]) < 1:
                nfast += 1
                with open("./proxies/fast.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif float(proxy[2]) < 3:
                nmedium += 1
                with open("./proxies/medium.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif float(proxy[2]) < 7:
                nslow += 1
                with open("./proxies/slow.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
            elif float(proxy[2]) >= 7:
                nultraslow += 1
                with open("./proxies/ultraslow.txt", "a") as f:
                    f.write(f"{proxy[0]}\n")
        with open("./README.md", "r") as f:
            readme = f.read()
        readme = readme.replace("#var-working", f"{all_proxies}").replace("#var-http", f"{nhttp}").replace(
            "#var-socks4", f"{nsocks4}").replace("#var-socks5", f"{nsocks5}").replace("#var-ultrafast", f"{nultrafast}").replace(
            "#var-fast", f"{nfast}").replace("#var-medium", f"{nmedium}").replace("#var-slow", f"{nslow}").replace(
            "#var-ultraslow", f"{nultraslow}").replace("#var-excluded", f"{nexcluded}").replace(
            "#var-misconfigured", f"{nmisconfigured}")
        with open("./README.md", "w") as f:
            f.write(readme)

def addold():
    with open("./proxies/all.txt", "r") as f:
        nodups = f.readlines()
    with open("./proxies/working-lastrun.txt", "r") as f:
        lastrun = f.read()
    nnew = 0
    new = ""
    for n in nodups:
        proxy = n.rstrip()
        if proxy not in lastrun:
            nnew += 1
            lastrun += proxy + "\n"
            new += proxy + "\n"
    with open("./README.md", "r") as f:
        readme = f.read()
    readme = readme.replace("#var-new", f"{nnew}")
    with open("./README.md", "w") as f:
        f.write(readme)
    with open("./proxies/new.txt", "w") as f:
        f.write(new)

def filterold():
    premium = ""
    npremium = 0
    with open("./proxies/working.txt", "r") as f:
        working = f.readlines()
    with open("./proxies/working-lastrun.txt", "r") as f:
        lastrun = f.read()
    for w in working:
        proxy = w.rstrip()
        if proxy in lastrun:
            npremium += 1
            premium += proxy + "\n"
    with open("./proxies/premium.txt", "w") as f:
        f.write(premium)
    with open("./README.md", "r") as f:
        readme = f.read()
    readme = readme.replace("#var-premium", f"{npremium}")
    with open("./README.md", "w") as f:
        f.write(readme)

def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_file_if_not_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w"):
            pass

def start():
    create_directory_if_not_exists("./proxies")
    create_file_if_not_exists("./Sources.txt")
    create_file_if_not_exists("./proxies/raw.txt")
    create_file_if_not_exists("./proxies/provider.csv")
    create_file_if_not_exists("./proxies/working.txt")

    with open("./Sources.txt", "r") as f:
        sources = f.readlines()

    with open("./proxies/working.txt", "r") as f:
        oldworking = f.read()

    with open("./proxies/working-lastrun.txt", "w") as f:
        f.write(oldworking)

    create_file_if_not_exists("./proxies/working.csv")
    create_file_if_not_exists("./proxies/misconfigured.csv")
    create_file_if_not_exists("./proxies/excluded.csv")

    threads = []
    log = ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for source in sources:
            rawurl = source.rstrip()
            if "://" in rawurl:
                if "[js]" in rawurl:
                    rawurl = rawurl.replace("[js]", "")
                    thread = executor.submit(gethtmljs, rawurl, log)
                    threads.append(thread)
                else:
                    thread = executor.submit(gethtml, rawurl, log)
                    threads.append(thread)

    for thread in threads:
        thread.result()

    normalizer()
    addold()

    threads = []
    log = ""
    with open("./proxies/all.txt", "r") as f:
        all_proxies = f.readlines()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for proxy in all_proxies:
            proxy = proxy.rstrip()
            thread = executor.submit(checker, proxy, log)
            threads.append(thread)

    for thread in threads:
        thread.result()

    createfiles()
    filterold()
    print("Finish")

proxy_pattern = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,5}\b")

start()
