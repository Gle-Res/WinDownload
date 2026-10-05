import json
import os
import sys
import subprocess
import urllib.request
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

# ================== 配置 ==================
JSON_URL = "https://raw.githubusercontent.com/Gle-Res/WinDownload/refs/heads/main/windows_links.json"

THUNDER_PATHS = [
    r"C:\Program Files (x86)\Thunder Network\Thunder\Program\Thunder.exe",
    r"C:\Program Files\Thunder Network\Thunder\Program\Thunder.exe",
    r"D:\Program Files (x86)\Thunder Network\Thunder\Program\Thunder.exe",
    r"D:\Program Files\Thunder Network\Thunder\Program\Thunder.exe",
    r"C:\Program Files (x86)\Thunder Network\Thunder\Program\ThunderStart.exe",
    r"C:\Program Files\Thunder Network\Thunder\Program\ThunderStart.exe",
]

# ================== 路径 ==================
APP_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


def resource_path(relative):
    """兼容 PyInstaller 打包后的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(APP_DIR, relative)


# ================== 主题 ==================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLOR_BG = "#f5f7fa"
COLOR_CARD = "#ffffff"
COLOR_ACCENT = "#3b82f6"
COLOR_ACCENT_HOVER = "#2563eb"
COLOR_TEXT = "#1f2937"
COLOR_TEXT_DIM = "#6b7280"
COLOR_SUCCESS = "#10b981"
COLOR_WARN = "#f59e0b"
COLOR_DANGER = "#ef4444"
COLOR_BORDER = "#e5e7eb"

UI_TEXT = {
    "zh": {
        "title": "Windows 镜像下载器",
        "subtitle": "通过迅雷下载 BT / ED2K 镜像",
        "system_label": "系统版本",
        "lang_label": "下载语言",
        "lang_zh": "中文版",
        "lang_en": "英文版",
        "start": "开始下载",
        "copy_done": "链接已复制到剪贴板，正在唤起迅雷…",
        "unsupported_title": "暂不支持",
        "unsupported_msg": "{name} · {lang} 暂不支持下载该版本",
        "author_stopped_title": "支持已终止",
        "author_stopped_msg": "作者已终止对该程序的支持。",
        "build": "构建号",
        "edition": "版本",
        "type": "类型",
        "error": "错误",
        "copy_fail": "复制到剪贴板失败：{err}",
        "no_thunder_title": "找不到迅雷",
        "no_thunder_msg": (
            "未检测到已安装的迅雷。\n\n"
            "请手动安装迅雷，或先打开迅雷后再点击下载。\n\n"
            "链接已复制到剪贴板，你也可以手动粘贴到迅雷中新建任务。"
        ),
        "no_thunder_status": "未找到迅雷，链接已复制到剪贴板，请手动打开迅雷粘贴",
    },
    "en": {
        "title": "Windows Image Downloader",
        "subtitle": "Download BT / ED2K images via Thunder",
        "system_label": "System",
        "lang_label": "Language",
        "lang_zh": "Chinese",
        "lang_en": "English",
        "start": "Start Download",
        "copy_done": "Link copied. Launching Thunder…",
        "unsupported_title": "Not Supported",
        "unsupported_msg": "{name} · {lang} is not supported yet",
        "author_stopped_title": "Support Ended",
        "author_stopped_msg": "The author has ended support for this program.",
        "build": "Build",
        "edition": "Edition",
        "type": "Type",
        "error": "Error",
        "copy_fail": "Failed to copy to clipboard: {err}",
        "no_thunder_title": "Thunder Not Found",
        "no_thunder_msg": (
            "Thunder is not installed or could not be located.\n\n"
            "Please install Thunder, or open Thunder first and click Download again.\n\n"
            "The link has been copied to your clipboard. "
            "You can also paste it into Thunder manually."
        ),
        "no_thunder_status": "Thunder not found. Link copied. Please open Thunder and paste.",
    }
}


# ================== 工具 ==================
def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WinImageDownloader/4.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def find_thunder():
    """多路径查找迅雷可执行文件，找不到返回 None"""
    for p in THUNDER_PATHS:
        if os.path.isfile(p):
            return p

    if os.name == "nt":
        try:
            import winreg
            keys = [
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Thunder.exe"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\Thunder.exe"),
                (winreg.HKEY_CURRENT_USER,
                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Thunder.exe"),
            ]
            for hive, path in keys:
                try:
                    with winreg.OpenKey(hive, path) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and os.path.isfile(val):
                            return val
                except OSError:
                    continue
        except Exception:
            pass

    try:
        result = subprocess.run(["where", "Thunder.exe"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().splitlines()
            if lines and os.path.isfile(lines[0]):
                return lines[0]
    except Exception:
        pass

    return None


def launch_thunder(link):
    copy_err = ""
    try:
        root = tk._default_root
        if root is not None:
            root.clipboard_clear()
            root.clipboard_append(link)
            root.update()
    except Exception as e:
        copy_err = str(e)

    thunder = find_thunder()
    if not thunder:
        return ("nothunder", copy_err)

    try:
        subprocess.Popen([thunder, link], shell=False)
        return ("ok", "")
    except Exception as e:
        return ("nothunder", str(e))


# ================== 主应用 ==================
class App(ctk.CTk):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.versions = data.get("versions", [])
        self.ui_lang = "zh"
        self.lang_download = "zh"

        self._set_icon()
        self._build_ui()
        self._refresh_lang()
        self._refresh_versions()
        self._on_system_change()

    def _set_icon(self):
        """加载 icon.ico，兼容打包后路径"""
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    # ---------- UI ----------
    def _build_ui(self):
        self.geometry("660x560")
        self.minsize(660, 560)
        self.configure(fg_color=COLOR_BG)
        self.title("Windows Image Downloader")

        # ===== 顶栏 =====
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(24, 0))

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", anchor="w")

        self.title_label = ctk.CTkLabel(
            left, text="", font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLOR_TEXT
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            left, text="", font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_DIM
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.lang_switch = ctk.CTkSegmentedButton(
            top, values=["中文", "EN"], command=self._on_ui_lang_switch,
            font=ctk.CTkFont(family="Segoe UI", size=12), height=32
        )
        self.lang_switch.pack(side="right", anchor="ne")
        self.lang_switch.set("中文")

        # ===== 版本选择卡片 =====
        self.system_card = self._make_selector_card("")
        self.system_card.pack(fill="x", padx=28, pady=(22, 0))

        # ===== 下载语言选择卡片 =====
        self.lang_card = self._make_selector_card("")
        self.lang_card.pack(fill="x", padx=28, pady=(12, 0))

        # ===== 信息条 =====
        info_bar = ctk.CTkFrame(self, fg_color="transparent")
        info_bar.pack(fill="x", padx=28, pady=(14, 0))

        self.build_chip = ctk.CTkLabel(
            info_bar, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_DIM, fg_color=COLOR_CARD,
            corner_radius=8, padx=12, pady=6
        )
        self.build_chip.pack(side="left")

        self.edition_chip = ctk.CTkLabel(
            info_bar, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_DIM, fg_color=COLOR_CARD,
            corner_radius=8, padx=12, pady=6
        )
        self.edition_chip.pack(side="left", padx=(8, 0))

        self.type_chip = ctk.CTkLabel(
            info_bar, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_DIM, fg_color=COLOR_CARD,
            corner_radius=8, padx=12, pady=6
        )
        self.type_chip.pack(side="left", padx=(8, 0))

        # ===== 状态提示 =====
        self.status_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_DIM,
            wraplength=600, justify="left"
        )
        self.status_label.pack(fill="x", padx=28, pady=(18, 0))

        # ===== 下载按钮 =====
        self.download_btn = ctk.CTkButton(
            self, text="", command=self._start_download,
            height=52, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            text_color="#ffffff"
        )
        self.download_btn.pack(fill="x", padx=28, pady=(24, 28))

    def _make_selector_card(self, label_text):
        card = ctk.CTkFrame(
            self, fg_color=COLOR_CARD, corner_radius=12,
            border_width=1, border_color=COLOR_BORDER
        )
        card.columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            card, text=label_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_DIM, anchor="w"
        )
        label.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        option = ctk.CTkOptionMenu(
            card, values=["—"], command=None,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#eef2f7", button_color="#eef2f7",
            button_hover_color="#e2e8f0",
            text_color=COLOR_TEXT,
            dropdown_text_color=COLOR_TEXT,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color="#eef2f7",
            corner_radius=8, height=42, anchor="w"
        )
        option.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        card.label = label
        card.option = option
        return card

    # ---------- 语言 ----------
    def _t(self, key, **kw):
        txt = UI_TEXT[self.ui_lang].get(key, key)
        return txt.format(**kw) if kw else txt

    def _on_ui_lang_switch(self, value):
        self.ui_lang = "zh" if value == "中文" else "en"
        self._refresh_lang()
        self._refresh_versions()
        self._on_system_change()

    def _refresh_lang(self):
        t = self._t
        self.title(t("title"))
        self.title_label.configure(text=t("title"))
        self.subtitle_label.configure(text=t("subtitle"))
        self.system_card.label.configure(text=t("system_label"))
        self.lang_card.label.configure(text=t("lang_label"))
        self.download_btn.configure(text=t("start"))

        opts = [t("lang_zh"), t("lang_en")]
        self.lang_card.option.configure(values=opts)
        self.lang_card.option.set(opts[0] if self.lang_download == "zh" else opts[1])
        self.lang_card.option.configure(command=self._on_dl_lang_change)
        self.system_card.option.configure(command=self._on_system_change)

    def _refresh_versions(self):
        displays = [self._version_display(v) for v in self.versions]
        if not displays:
            displays = ["—"]
        self.system_card.option.configure(values=displays)
        cur = self.system_card.option.get()
        self.system_card.option.set(cur if cur in displays else displays[0])

    def _version_display(self, v):
        name = v.get(f"name_{self.ui_lang}") or v.get("name_zh") or v.get("id", "?")
        edition = v.get("edition", "")
        return f"{name}  [{edition}]" if edition else name

    def _selected_version(self):
        cur = self.system_card.option.get()
        for v in self.versions:
            if self._version_display(v) == cur:
                return v
        return None

    def _get_link_info(self):
        v = self._selected_version()
        if not v:
            return "", ""
        entry = v.get("links", {}).get(self.lang_download, {})
        if isinstance(entry, str):
            return ("bt", entry.strip()) if entry.strip() else ("", "")
        if not isinstance(entry, dict):
            return "", ""
        return entry.get("type", "bt").lower(), (entry.get("url", "") or "").strip()

    def _on_system_change(self, *_):
        v = self._selected_version()
        if not v:
            self.build_chip.configure(text="")
            self.edition_chip.configure(text="")
            self.type_chip.configure(text="")
            return
        self.build_chip.configure(text=f"{self._t('build')}  {v.get('build', '-')}")
        self.edition_chip.configure(text=f"{self._t('edition')}  {v.get('edition', '-')}")

        link_type, url = self._get_link_info()
        if not url:
            self.type_chip.configure(text="—", text_color=COLOR_TEXT_DIM)
        elif link_type == "ed2k":
            self.type_chip.configure(text="ED2K", text_color=COLOR_WARN)
        else:
            self.type_chip.configure(text="BT", text_color=COLOR_SUCCESS)

    def _on_dl_lang_change(self, value):
        self.lang_download = "zh" if value == self._t("lang_zh") else "en"
        self._on_system_change()

    # ---------- 下载 ----------
    def _start_download(self):
        v = self._selected_version()
        if not v:
            return

        link_type, url = self._get_link_info()
        if not url:
            name = self._version_display(v)
            lang_text = self._t("lang_zh") if self.lang_download == "zh" else self._t("lang_en")
            messagebox.showinfo(
                self._t("unsupported_title"),
                self._t("unsupported_msg", name=name, lang=lang_text)
            )
            return

        status, info = launch_thunder(url)

        if status == "ok":
            self.status_label.configure(
                text=self._t("copy_done"), text_color=COLOR_SUCCESS
            )
        elif status == "nocopy":
            messagebox.showerror(
                self._t("error"), self._t("copy_fail", err=info)
            )
            self.status_label.configure(
                text=self._t("copy_fail", err=info), text_color=COLOR_DANGER
            )
        else:  # nothunder
            messagebox.showwarning(
                self._t("no_thunder_title"),
                self._t("no_thunder_msg")
            )
            self.status_label.configure(
                text=self._t("no_thunder_status"), text_color=COLOR_WARN
            )


# ================== 入口 ==================
def main():
    root = tk.Tk()
    root.withdraw()
    tk._default_root = root

    data = fetch_json(JSON_URL)
    if not data or "versions" not in data:
        messagebox.showerror(
            UI_TEXT["zh"]["author_stopped_title"],
            UI_TEXT["zh"]["author_stopped_msg"] + "\n\n"
            + UI_TEXT["en"]["author_stopped_msg"]
        )
        root.destroy()
        return

    root.destroy()
    app = App(data)
    app.mainloop()


if __name__ == "__main__":
    main()