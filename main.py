import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select as SeleniumSelect
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException, WebDriverException,
)
from colorama import Fore, Style, init
from pystyle import *
import requests
import time
import random
import string
import re
import subprocess
import os
import sys
import json
import calendar
from datetime import datetime
import tls_client
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
MAX_ACCOUNTS = 0            # 0 = infinite
DISPLAY_NAME = "Lunarxterm"
CAPTCHA_TIMEOUT = 240       # seconds to wait for a solve
CAPTCHA_POLL = 5            # seconds between polls
TOKEN_FILES = ("tokens.txt", "evs.txt")

CAPTCHA_BASES = {
    "2Captcha": "https://2captcha.com",
    "9Captcha": "https://9captcha.com",
}

banner = f'''
████▄  ██████ ▄████  
██  ██   ██  ██  ▄▄▄ 
████▀    ██   ▀███▀  

[+] By HunterTheDev
[+] Discord:@zen_x_2
'''


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def chrome_v():
    if os.name == "nt":
        out = subprocess.run(
            r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
            capture_output=True, text=True, shell=True
        ).stdout
        m = re.search(r"(\d+)\.", out)
        if m:
            return int(m.group(1))

    for cmd in (["chromium", "--version"],
                ["chromium-browser", "--version"],
                ["google-chrome", "--version"]):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            m = re.search(r"(\d+)\.", res.stdout or res.stderr)
            if m:
                return int(m.group(1))
        except FileNotFoundError:
            continue

    return None


def random_sleep(base=2, variation=3):
    time.sleep(base + random.uniform(0, variation))


def timestamp():
    return f"{Fore.LIGHTBLACK_EX}[{datetime.now().strftime('%H:%M:%S %d-%m-%Y')}]"


def log(msg, color=Fore.CYAN):
    print(f"{timestamp()} {color}{msg}{Style.RESET_ALL}", flush=True)


def account_ratelimit():
    """Probes the register endpoint and returns retry_after seconds (>= 0)."""
    client = tls_client.Session(client_identifier="chrome_110")
    client.headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "DNT": "1",
        "Host": "discord.com",
        "Origin": "https://discord.com",
        "Referer": "https://discord.com/register",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "X-Debug-Options": "bugReporterEnabled",
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "Asia/Calcutta",
        "X-Super-Properties": (
            "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIEZyYW1lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImdyLUFSIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS80LjAgKGNvbXBhdGlibGU7IE1TSUUgOC4wOyBXaW5kb3dzIE5UIDYuMTsgVHJpZGVudC80LjA7IEdUQjcuNDsgY2hyb21lZnJhbWUvMjQuMC4xMzEyLjU3OyBTTENDMjsgLk5FVCBDTFIgMi4wLjUwNzI3OyAuTkVUIENMUiAzLjUuMzA3Mjk7IC5ORVQgQ0xSIDMuMC4zMDcyOTsgLk5FVDQuMEM7IEluZm9QYXRoLjM7IE1TLVJUQyBMTSA4OyBCUkkvMikiLCJicm93c2VyX3ZlcnNpb24iOiIyNC4wLjEzMTIiLCJvc192ZXJzaW9uIjoiNyIsInJlZmVycmVyIjoiaHR0cHM6Ly93d3cueW91dHViZS5jb20vIiwicmVmZXJyaW5nX2RvbWFpbiI6Ind3dy55b3V0dWJlLmNvbSIsInNlYXJjaF9lbmdpbmUiOiJhc2suY29tIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjE0ODQ3OSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
        ),
    }
    local = "".join(random.choices(string.ascii_lowercase, k=9)) + "".join(random.choices(string.digits, k=6))
    data = {
        "email": local,
        "password": "ultimate12$$",
        "date_of_birth": "2000-09-20",
        "username": local,
        "consent": True,
        "captcha_service": "hcaptcha",
        "global_name": "ultimate",
        "captcha_key": None,
        "invite": None,
        "promotional_email_opt_in": False,
        "gift_code_sku_id": None,
    }
    try:
        req = client.post("https://discord.com/api/v9/auth/register", json=data)
        if req.status_code == 429 or "rate limited" in req.text.lower():
            try:
                return float(req.json().get("retry_after", 1))
            except Exception:
                return 1.0
        return 0.0
    except Exception as e:
        log(f"Rate limit probe failed: {e}", Fore.YELLOW)
        return 0.0


# ---------------------------------------------------------------------------
# IDENTITY
# ---------------------------------------------------------------------------
def generate_identity():
    uname = "".join(random.choices(string.ascii_lowercase, k=3)) + \
            "".join(random.choices(string.ascii_lowercase + string.digits + "._", k=8))
    email = "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@gmail.com"
    pw = "".join(random.choices(string.ascii_letters + string.digits, k=9)) + \
         random.choice("!@#$%^&*") + \
         "".join(random.choices(string.digits, k=3))
    return uname, email, pw


def generate_random_dob():
    year = random.randint(1975, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, calendar.monthrange(year, month)[1])
    return month, day, year


# ---------------------------------------------------------------------------
# CAPTCHA SOLVING (2Captcha-compatible API)
# ---------------------------------------------------------------------------
def _solver_parse(text):
    """Parses both JSON and pipe-delimited solver responses."""
    text = (text or "").strip()
    try:
        j = json.loads(text)
        return str(j.get("status")), str(j.get("request"))
    except Exception:
        if "|" in text:
            status, _, payload = text.partition("|")
            return status.strip(), payload.strip()
        return "0", text


def solve_hcaptcha(api_key, base_url, sitekey, page_url, timeout=CAPTCHA_TIMEOUT):
    submit = {
        "key": api_key,
        "method": "hcaptcha",
        "sitekey": sitekey,
        "pageurl": page_url,
        "json": 1,
    }
    try:
        r = requests.post(f"{base_url}/in.php", data=submit, timeout=30)
    except Exception as e:
        log(f"Captcha submit failed: {e}", Fore.RED)
        return None

    status, task_id = _solver_parse(r.text)
    if status != "1":
        log(f"Captcha submit rejected: {task_id}", Fore.RED)
        return None

    log(f"Captcha task {task_id} queued, polling...", Fore.YELLOW)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(CAPTCHA_POLL)
        try:
            r = requests.get(
                f"{base_url}/res.php",
                params={"key": api_key, "action": "get", "id": task_id, "json": 1},
                timeout=30,
            )
        except Exception:
            continue

        status, payload = _solver_parse(r.text)
        if status == "1":
            return payload
        if payload.upper() in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
            continue
        if payload.upper().startswith("ERROR"):
            log(f"Captcha error: {payload}", Fore.RED)
            return None

    log("Captcha timed out.", Fore.RED)
    return None


def get_hcaptcha_sitekey(driver):
    try:
        for ifr in driver.find_elements(By.CSS_SELECTOR, "iframe[src*='sitekey=']"):
            m = re.search(r"sitekey=([0-9a-zA-Z-]{20,})", ifr.get_attribute("src") or "")
            if m:
                return m.group(1)
    except WebDriverException:
        pass
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, "[data-sitekey], .h-captcha"):
            sk = el.get_attribute("data-sitekey")
            if sk:
                return sk
    except WebDriverException:
        pass
    return None


INJECT_JS = """
const token = arguments[0];
let ok = false;
for (const name of ['h-captcha-response', 'g-recaptcha-response']) {
    const ta = document.querySelector('textarea[name="' + name + '"]');
    if (ta) {
        ta.value = token;
        ta.dispatchEvent(new Event('input', { bubbles: true }));
        ta.dispatchEvent(new Event('change', { bubbles: true }));
        ta.dispatchEvent(new Event('blur', { bubbles: true }));
        ok = true;
    }
}
document.querySelectorAll('button[type="submit"]').forEach(b => {
    if (b.disabled) { b.disabled = false; b.removeAttribute('disabled'); }
});
return ok;
"""


def inject_captcha_token(driver, token, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if driver.execute_script(INJECT_JS, token):
                return True
        except WebDriverException:
            pass
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# DOB (native selects, then label-addressed fields with verification)
# ---------------------------------------------------------------------------
DOB_FIELD_KEYS = {
    "month": ("month", "month of birth", "birth month", "mm"),
    "day": ("day", "day of birth", "birth day", "dd"),
    "year": ("year", "year of birth", "birth year", "yyyy"),
}

DOB_ATTRS = ("aria-label", "placeholder", "name", "id", "title",
             "autocomplete", "aria-labelledby")


def _field_blob(el):
    parts = []
    for a in DOB_ATTRS:
        try:
            v = el.get_attribute(a)
        except StaleElementReferenceException:
            return []
        if v:
            parts.append(" ".join(v.split()).strip().lower())
    return parts


def _field_value(el):
    try:
        v = el.get_attribute("value")
        if v:
            return v.strip()
        return " ".join(el.text.split()).strip()
    except StaleElementReferenceException:
        return ""


def _value_ok(val, candidates):
    if not val:
        return False
    low = val.lower()
    for c in candidates:
        cl = c.lower()
        if low == cl:
            return True
        if c.isdigit() and low.isdigit() and low.lstrip("0") == c.lstrip("0"):
            return True
        if len(c) >= 3 and low.startswith(cl):
            return True
    return False


def menu_open(driver):
    try:
        for el in driver.find_elements(
            By.XPATH, '//*[@role="listbox"] | //*[@role="menu"] | //*[@role="option"]'
        ):
            if el.is_displayed():
                return True
    except WebDriverException:
        pass
    return False


def find_dob_field(driver, kind):
    """Locates one DOB field by its label attributes. Never positional."""
    keys = DOB_FIELD_KEYS[kind]
    try:
        els = driver.find_elements(
            By.XPATH,
            "//input[not(@type) or @type='text' or @type='number'] | //*[@role='combobox']"
        )
    except WebDriverException:
        return None

    visible = []
    for el in els:
        try:
            if not el.is_displayed():
                continue
            blob = _field_blob(el)
        except StaleElementReferenceException:
            continue
        if blob:
            visible.append((el, blob))

    for el, blob in visible:                       # exact attribute match wins
        if any(b == k for b in blob for k in keys):
            return el
    for el, blob in visible:                       # then substring match
        joined = " ".join(blob)
        if any(k in joined for k in keys):
            return el
    return None


def find_three_dob_row(driver):
    """Positional fallback: three controls in one horizontal row, ordered by X."""
    def collect(xpath, wmin, wmax, hmin, hmax):
        out = []
        for el in driver.find_elements(By.XPATH, xpath):
            try:
                if not el.is_displayed():
                    continue
                r = el.rect
                if wmin <= r["width"] <= wmax and hmin <= r["height"] <= hmax:
                    out.append((el, r))
            except StaleElementReferenceException:
                continue
        return out

    items = collect('//*[@role="combobox"]', 20, 400, 15, 90)
    if len(items) < 3:
        items = collect(
            '//div[@role="button"] | //button | '
            '//div[contains(@class,"select") or contains(@class,"dropdown") or contains(@class,"control")]',
            30, 360, 22, 85
        )

    unique = []
    for el, r in items:
        if not any(abs(r["x"] - u["x"]) < 8 and abs(r["y"] - u["y"]) < 8
                   and abs(r["width"] - u["width"]) < 12 for _, u in unique):
            unique.append((el, r))

    rows = {}
    for el, r in unique:
        rows.setdefault(round(r["y"] / 15) * 15, []).append((el, r))

    for key in sorted(rows):
        row = sorted(rows[key], key=lambda x: x[1]["x"])
        if len(row) >= 3:
            return [x[0] for x in row[:3]]
    return None


def type_into(driver, el, text):
    """Types into a real text input, with a React-safe value setter fallback."""
    try:
        driver.execute_script("arguments[0].focus();", el)
        el.send_keys(Keys.CONTROL, "a")
        el.send_keys(Keys.BACKSPACE)
        el.send_keys(text)
        time.sleep(0.2)
        if _value_ok(_field_value(el), [text]):
            return True
    except WebDriverException:
        pass

    try:
        driver.execute_script(
            """
            const el = arguments[0], val = arguments[1];
            const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
            Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, val);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            el, text
        )
        time.sleep(0.2)
        return _value_ok(_field_value(el), [text])
    except WebDriverException:
        return False


def select_option_by_values(select_el, candidates):
    sel = SeleniumSelect(select_el)
    options = sel.options
    lower_cands = [c.lower() for c in candidates]

    for cand in lower_cands:
        for opt in options:
            if " ".join(opt.text.split()).strip().lower() == cand or \
               (opt.get_attribute("value") or "").strip().lower() == cand:
                sel.select_by_visible_text(opt.text)
                return True

    for cand in lower_cands:
        if cand.isdigit():
            for opt in options:
                t = " ".join(opt.text.split()).strip()
                v = (opt.get_attribute("value") or "").strip()
                if (t.isdigit() and str(int(t)) == str(int(cand))) or \
                   (v.isdigit() and str(int(v)) == str(int(cand))):
                    sel.select_by_visible_text(opt.text)
                    return True
    return False


def pick_option_with_scroll(driver, trigger, candidates, label):
    wanted = {c.lower() for c in candidates}
    opt_xpath = (
        '//*[@role="option"] | //*[@role="menuitem"] | '
        '//*[@role="listbox"]//*[self::div or self::span or self::li or self::button] | '
        '//*[contains(@class,"option") or contains(@class,"item") or contains(@class,"menu")]'
        '//*[self::div or self::span or self::li or self::button]'
    )
    containers = driver.find_elements(
        By.XPATH,
        '//*[@role="listbox"] | //*[@role="menu"] | '
        '//*[contains(@class,"menu") or contains(@class,"listbox") or contains(@class,"dropdown")]'
    )

    deadline = time.time() + 10
    while time.time() < deadline:
        for el in driver.find_elements(By.XPATH, opt_xpath):
            try:
                if not el.is_displayed():
                    continue
                r = el.rect
                if r["height"] <= 0 or r["height"] > 120 or r["width"] < 15:
                    continue
                txt = " ".join(el.text.split()).strip()
                if txt.lower() in wanted:
                    deeper = [c for c in el.find_elements(By.XPATH, './/*')
                              if c.is_displayed()
                              and " ".join(c.text.split()).strip().lower() == txt.lower()]
                    if deeper:
                        continue
                    try:
                        el.click()
                    except WebDriverException:
                        driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.25)
                    log(f"{label} -> {txt}", Fore.CYAN)
                    return True
            except StaleElementReferenceException:
                continue

        scrolled = False
        for mc in containers:
            try:
                if not mc.is_displayed():
                    continue
                if driver.execute_script(
                    "if (arguments[0].scrollHeight > arguments[0].clientHeight) {"
                    " const p = arguments[0].scrollTop;"
                    " arguments[0].scrollTop = Math.min(arguments[0].scrollTop + 200,"
                    " arguments[0].scrollHeight);"
                    " return arguments[0].scrollTop !== p; } return false;", mc):
                    scrolled = True
            except StaleElementReferenceException:
                continue

        if not scrolled:
            # keyboard navigation needs focus back on the trigger
            try:
                driver.execute_script("arguments[0].focus();", trigger)
                ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
            except WebDriverException:
                pass
        time.sleep(0.12)

    # last resort: focus the trigger, type the value, confirm
    try:
        driver.execute_script("arguments[0].focus();", trigger)
        ActionChains(driver).send_keys(candidates[0]).pause(0.2).send_keys(Keys.RETURN).perform()
        time.sleep(0.3)
        log(f"{label} -> typed {candidates[0]}", Fore.YELLOW)
        return True
    except WebDriverException:
        return False


def set_dob_field(driver, el, candidates, label):
    """Clicks one specific field, sets it, and verifies the read-back value."""
    for _ in range(3):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.1)
            try:
                el.click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", el)
            time.sleep(0.35)
        except StaleElementReferenceException:
            time.sleep(0.2)
            continue

        try:
            if menu_open(driver):
                if pick_option_with_scroll(driver, el, candidates, label):
                    try:
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except WebDriverException:
                        pass
                    time.sleep(0.2)
                    if _value_ok(_field_value(el), candidates):
                        return True
                    log(f"{label}: menu pick didn't stick, retrying.", Fore.YELLOW)
            else:
                if type_into(driver, el, candidates[0]):
                    log(f"{label} -> {_field_value(el)}", Fore.CYAN)
                    return True
                # read-only combobox that ignores typing: nudge with arrows
                try:
                    driver.execute_script("arguments[0].focus();", el)
                    ActionChains(driver).send_keys(Keys.ARROW_DOWN, Keys.RETURN).perform()
                    time.sleep(0.25)
                    if _value_ok(_field_value(el), candidates):
                        return True
                except WebDriverException:
                    pass
        except (WebDriverException, StaleElementReferenceException):
            pass
        time.sleep(0.25)
    return False


def fill_date_of_birth(driver, month, day, year):
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    target_month = month_names[month - 1]

    selects = driver.find_elements(By.TAG_NAME, "select")
    if len(selects) >= 3:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selects[0])
        time.sleep(0.15)
        if (select_option_by_values(selects[0], [target_month, target_month[:3], str(month)])
                and select_option_by_values(selects[1], [str(day), f"{day:02d}"])
                and select_option_by_values(selects[2], [str(year)])):
            log(f"Date set via selects ({target_month} {day}, {year}).", Fore.GREEN)
            return

    targets = [
        ("month", [target_month, target_month[:3], str(month), f"{month:02d}"]),
        ("day", [str(day), f"{day:02d}"]),
        ("year", [str(year)]),
    ]

    def resolve_fields():
        found = {kind: find_dob_field(driver, kind) for kind, _ in targets}
        if len({id(v) for v in found.values() if v is not None}) == 3:
            return found
        row = find_three_dob_row(driver)
        if row and len(row) == 3:
            return {"month": row[0], "day": row[1], "year": row[2]}
        return None

    fields = WebDriverWait(driver, 20).until(lambda d: resolve_fields())

    for kind, cands in targets:
        ok = False
        for _ in range(3):
            el = find_dob_field(driver, kind) or fields.get(kind)
            if el is None:
                fields = resolve_fields() or fields
                el = fields.get(kind)
            if el is None:
                continue
            if set_dob_field(driver, el, cands, kind):
                ok = True
                break
            fields = resolve_fields() or fields
        if not ok:
            raise TimeoutException(f"Failed setting {kind} -> {cands[0]}")

    log(f"Date set ({target_month} {day}, {year}).", Fore.GREEN)


# ---------------------------------------------------------------------------
# TOKEN
# ---------------------------------------------------------------------------
def save_token(email, password, token):
    with open(TOKEN_FILES[0], "a", encoding="utf-8") as f:
        f.write(token + "\n")
    with open(TOKEN_FILES[1], "a", encoding="utf-8") as f:
        f.write(f"{email}:{password}:{token}\n")
    log("Token saved to tokens.txt and evs.txt", Fore.GREEN)


def fetch_token_from_browser(driver, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            raw = driver.execute_script(
                "try { return window.localStorage.getItem('token'); } catch (e) { return null; }"
            )
            if raw:
                try:
                    token = json.loads(raw)
                except Exception:
                    token = raw.strip('"')
                if token:
                    return token
        except WebDriverException:
            pass
        time.sleep(1)
    return None


def login_and_fetch_token(email, password):
    data = {"login": email, "password": password, "undelete": "false"}
    headers = {
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "origin": "https://discord.com",
        "referer": "https://discord.com/login",
        "x-debug-options": "bugReporterEnabled",
    }
    try:
        r = requests.post("https://discord.com/api/v9/auth/login",
                          json=data, headers=headers, timeout=30)
    except requests.exceptions.RequestException as e:
        log(f"Login connection error: {e}", Fore.RED)
        return None

    if r.status_code == 200:
        return r.json().get("token")

    if "captcha" in r.text.lower():
        log("Fallback login blocked by captcha.", Fore.YELLOW)
    else:
        log(f"Fallback login failed ({r.status_code}): {r.text[:200]}", Fore.RED)
    return None


# ---------------------------------------------------------------------------
# PROMPT
# ---------------------------------------------------------------------------
def prompt_captcha_config():
    print(f"{Fore.CYAN}Which captcha solver do you wanna use?{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1 = 2Captcha{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}2 = 9Captcha{Style.RESET_ALL}")
    print(f"{Fore.RED}0 = Cancel{Style.RESET_ALL}")

    while True:
        choice = input(f"{Fore.GREEN}Select option [1 / 2 / 0]: {Style.RESET_ALL}").strip()
        if choice == "0":
            log("Cancelled by user.", Fore.YELLOW)
            sys.exit(0)
        if choice in ("1", "2"):
            name = "2Captcha" if choice == "1" else "9Captcha"
            break
        print(f"{Fore.RED}Invalid choice. Enter 1, 2, or 0.{Style.RESET_ALL}")

    api_key = input(
        f"{Fore.GREEN}Enter your {name} API key "
        f"(leave blank for manual solving): {Style.RESET_ALL}"
    ).strip()

    if api_key:
        log(f"Solver: {name} | key configured.", Fore.CYAN)
    else:
        log("No key given - you'll solve captchas manually.", Fore.YELLOW)
    return name, api_key


# ---------------------------------------------------------------------------
# ONE ACCOUNT
# ---------------------------------------------------------------------------
def run_account(base_url, api_key):
    username, email, password = generate_identity()
    log(f"Identity: {email} / {username}", Fore.BLUE)

    driver = None
    token = None
    try:
        options = uc.ChromeOptions()
        for arg in ("--disable-popup-blocking", "--no-sandbox", "--disable-dev-shm-usage",
                    "--ignore-certificate-errors", "--lang=en-US",
                    "--disable-blink-features=AutomationControlled"):
            options.add_argument(arg)
        options.add_experimental_option("prefs", {"intl.accept_languages": "en-US,en"})

        driver = uc.Chrome(options=options, version_main=chrome_v())
        driver.maximize_window()

        log("Opening register page...", Fore.BLUE)
        driver.get("https://discord.com/register")
        WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.NAME, "email")))

        driver.find_element(By.NAME, "email").send_keys(email)
        driver.find_element(By.NAME, "global_name").send_keys(DISPLAY_NAME)
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        log("Form filled.", Fore.CYAN)

        month, day, year = generate_random_dob()
        try:
            fill_date_of_birth(driver, month, day, year)
        except Exception as e:
            log(f"DOB step failed ({month}/{day}/{year}): {e}", Fore.RED)
            raise

        try:
            boxes = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//input[@type='checkbox']"))
            )
            for box in boxes:
                if not box.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", box)
            log(f"Ticked {len(boxes)} checkbox(es).", Fore.CYAN)
        except Exception as e:
            log(f"Checkbox step failed (continuing): {e}", Fore.YELLOW)

        # ---- captcha ----
        if api_key:
            sitekey = get_hcaptcha_sitekey(driver)
            if sitekey:
                log(f"Sitekey found: {sitekey}", Fore.CYAN)
                solved = solve_hcaptcha(api_key, base_url, sitekey, driver.current_url)
                if solved:
                    if inject_captcha_token(driver, solved):
                        log("Captcha token injected.", Fore.GREEN)
                        time.sleep(1.0)
                    else:
                        log("Injection failed - response field never appeared.", Fore.YELLOW)
                else:
                    log("Solver returned nothing - falling back to manual.", Fore.YELLOW)
            else:
                log("No hCaptcha sitekey found - falling back to manual.", Fore.YELLOW)

        retry_after = account_ratelimit()
        if retry_after > 1:
            log(f"Rate limited, sleeping {retry_after:.0f}s.", Fore.RED)
            time.sleep(retry_after)

        submit = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]'))
        )
        submit.click()
        log("Submitted - waiting for redirect (solve manually if needed)...", Fore.BLUE)

        WebDriverWait(driver, 300).until(EC.url_contains("discord.com/channels/@me"))
        log("Registered and logged in.", Fore.GREEN)

        token = fetch_token_from_browser(driver)
        if not token:
            log("Could not read token from browser storage, trying HTTP login.", Fore.YELLOW)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            driver = None

    if not token:
        token = login_and_fetch_token(email, password)

    if token:
        save_token(email, password, token)
        return True

    log("Token acquisition failed.", Fore.RED)
    return False


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print(Colorate.Vertical(Colors.purple_to_blue, Center.XCenter(banner)))
    solver_name, api_key = prompt_captcha_config()
    base_url = CAPTCHA_BASES.get(solver_name, CAPTCHA_BASES["2Captcha"])

    created = 0
    attempt = 0
    while True:
        if MAX_ACCOUNTS and created >= MAX_ACCOUNTS:
            log(f"Reached limit of {MAX_ACCOUNTS} account(s). Done.", Fore.GREEN)
            break
        attempt += 1
        log(f"--- Attempt #{attempt} (created: {created}) ---", Fore.MAGENTA)
        try:
            if run_account(base_url, api_key):
                created += 1
        except KeyboardInterrupt:
            log(f"Interrupted. {created} account(s) created.", Fore.YELLOW)
            break
        except Exception as e:
            log(f"Attempt failed: {type(e).__name__}: {e}", Fore.RED)
        random_sleep(3, 4)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Shutdown.", Fore.YELLOW)
