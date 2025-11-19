import os
from typing import Optional

import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ---------- CONFIG ----------
OPENSUBTITLES_API_URL = "https://api.opensubtitles.com/api/v1"

# Use env var if set, otherwise fall back to your key
OPENSUBTITLES_API_TOKEN = os.getenv("OPENSUBTITLES_API_KEY")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "subtitles")
ICON_PATH = os.path.join(PROJECT_ROOT, "assets", "icon.ico")

USER_AGENT = "SubtitleDownloader v1.0"

USER_JWT_TOKEN = None


# ---------- API HELPERS ----------
def _get_headers() -> dict:
    """Common headers for all OpenSubtitles API requests."""
    if not OPENSUBTITLES_API_TOKEN:
        raise RuntimeError("OpenSubtitles API key is missing.")
    headers = {
        "Api-Key": OPENSUBTITLES_API_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if USER_JWT_TOKEN:
        headers["Authorization"] = f"Bearer {USER_JWT_TOKEN}"
    return headers


def search_subtitles(title: str, lang: str = "en"):
    """
    Search subtitles from OpenSubtitles by movie title and language.

    GET /subtitles
    """
    headers = _get_headers()
    params = {
        "query": title,
        "languages": lang,
        "order_by": "download_count",
        "order_direction": "desc",
        "type": "movie",
    }

    resp = requests.get(
        f"{OPENSUBTITLES_API_URL}/subtitles",
        headers=headers,
        params=params,
        timeout=15,
    )

    # Debug output for API response
    print("[DEBUG] Search subtitles response status:", resp.status_code)
    print("[DEBUG] Search subtitles response text:", resp.text)

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: check your API key or login.")
    if resp.status_code == 403:
        raise RuntimeError("Forbidden: check your API key or login.")
    if resp.status_code == 429:
        raise RuntimeError("Too many requests: rate limit exceeded.")
    resp.raise_for_status()

    data = resp.json()
    return data.get("data", [])


def download_subtitle_file(file_id: int, download_dir: str) -> str:
    """
    Download a subtitle file by file_id to download_dir.

    POST /download
    Body: { "file_id": <int> }
    Response has 'link' with the download URL.
    """
    headers = _get_headers()
    payload = {"file_id": file_id}

    # 1) Ask OpenSubtitles for a download link
    resp = requests.post(
        f"{OPENSUBTITLES_API_URL}/download",
        headers=headers,
        json=payload,
        timeout=15,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: check your API key.")
    if resp.status_code == 429:
        raise RuntimeError("Too many requests: rate limit exceeded.")
    resp.raise_for_status()

    info = resp.json()
    link = info.get("link")
    file_name = info.get("file_name", f"subtitle_{file_id}.srt")

    if not link:
        raise RuntimeError("No download link returned from API.")

    # 2) Download the actual subtitle file
    os.makedirs(download_dir, exist_ok=True)
    file_path = os.path.join(download_dir, file_name)

    file_resp = requests.get(link, timeout=30)
    file_resp.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(file_resp.content)

    return file_path


# ---------- GUI APP ----------
class SubtitleDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # CustomTkinter setup
        ctk.set_appearance_mode("dark")  # default dark theme
        ctk.set_default_color_theme("blue")

        self.title("Movie Subtitle Downloader")
        self.geometry("800x650")
        self.resizable(False, False)

        # Set icon if available (Windows-friendly)
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        # State
        self.subtitles_data = []
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.selected_index = ctk.IntVar(value=-1)

        self.username_entry = None
        self.password_entry = None
        self.jwt_token = None
        self.username = ""
        self.password = ""
        self._build_ui()

    # ---------- UI BUILD ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        left = ctk.CTkFrame(self, corner_radius=20)
        left.grid(row=0, column=0, padx=20, pady=20, sticky="ns")
        left.grid_rowconfigure(14, weight=1)

        # Username
        lbl_username = ctk.CTkLabel(left, text="OpenSubtitles Username:")
        lbl_username.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")
        self.username_entry = ctk.CTkEntry(left, width=220, placeholder_text="username")
        self.username_entry.grid(row=1, column=0, padx=20, pady=(0, 10))
        # Password
        lbl_password = ctk.CTkLabel(left, text="OpenSubtitles Password:")
        lbl_password.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")
        self.password_entry = ctk.CTkEntry(left, width=220, placeholder_text="password", show="*")
        self.password_entry.grid(row=3, column=0, padx=20, pady=(0, 10))
        # Login button
        btn_login = ctk.CTkButton(left, text="Login", command=self.on_login_clicked)
        btn_login.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")
        # Register button next to Login
        btn_register = ctk.CTkButton(left, text="Register", command=lambda: self.open_register_url())
        btn_register.grid(row=4, column=0, padx=(120, 20), pady=(10, 5), sticky="e")
        self.login_controls = [lbl_username, self.username_entry, lbl_password, self.password_entry, btn_login, btn_register]

        # Info label for login status
        self.login_status_label = ctk.CTkLabel(left, text="Please login to search and download subtitles.", text_color="#FFB347")
        self.login_status_label.grid(row=5, column=0, padx=20, pady=(10, 5))
        # Group login controls for easy hiding
        self.login_controls = [lbl_username, self.username_entry, lbl_password, self.password_entry, btn_login, btn_register, self.login_status_label]

        # Search controls (hidden until login)
        self.search_controls = []
        lbl_movie = ctk.CTkLabel(left, text="Movie title:")
        lbl_movie.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="w")
        self.search_controls.append(lbl_movie)
        self.movie_entry = ctk.CTkEntry(left, width=220, placeholder_text="e.g. Inception")
        self.movie_entry.grid(row=7, column=0, padx=20, pady=(0, 10))
        self.search_controls.append(self.movie_entry)
        # Language
        lbl_lang = ctk.CTkLabel(left, text="Language:")
        lbl_lang.grid(row=8, column=0, padx=20, pady=(10, 5), sticky="w")
        self.search_controls.append(lbl_lang)
        self.lang_option = ctk.CTkOptionMenu(left, values=["en", "es", "fr", "de", "it", "pt", "ru", "ko", "ja"], width=220)
        self.lang_option.set("en")
        self.lang_option.grid(row=9, column=0, padx=20, pady=(0, 10))
        self.search_controls.append(self.lang_option)
        # Folder
        btn_folder = ctk.CTkButton(left, text="Choose download folder", command=self.choose_folder)
        btn_folder.grid(row=10, column=0, padx=20, pady=(10, 5))
        self.search_controls.append(btn_folder)
        self.folder_label = ctk.CTkLabel(left, text=f"→ {self.download_dir}", wraplength=220, justify="left")
        self.folder_label.grid(row=11, column=0, padx=20, pady=(0, 10))
        self.search_controls.append(self.folder_label)
        # Search
        btn_search = ctk.CTkButton(left, text="Search Subtitles", command=self.on_search_clicked)
        btn_search.grid(row=12, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.search_controls.append(btn_search)
        # Theme switch
        self.theme_switch = ctk.CTkSwitch(left, text="Dark mode", command=self.toggle_theme)
        self.theme_switch.select()
        self.theme_switch.grid(row=13, column=0, padx=20, pady=(0, 20), sticky="s")

        # Footer copyright label
        footer_label = ctk.CTkLabel(
            left,
            text="© 2025 lahirusanjika | GitHub: github.com/lahirusanjika",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        footer_label.grid(row=14, column=0, padx=20, pady=(10, 5), sticky="s")

        # Hide search controls initially
        for widget in self.search_controls:
            widget.grid_remove()

        # RIGHT PANEL
        right = ctk.CTkFrame(self, corner_radius=20)
        right.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        lbl_results = ctk.CTkLabel(
            right,
            text="Results",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_results.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.results_box = ctk.CTkScrollableFrame(
            right, width=600, height=350
        )
        self.results_box.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")

        self.result_buttons = []

        btn_download = ctk.CTkButton(
            right,
            text="Download Selected Subtitle",
            command=self.on_download_clicked,
        )
        btn_download.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="e")

        self.status_label = ctk.CTkLabel(
            right,
            text="Enter a movie title and click Search.",
            anchor="w",
            justify="left",
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 5), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(
            right, mode="indeterminate"
        )
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progress_bar.grid_remove()

    # ---------- PROGRESS ----------
    def start_progress(self, text: Optional[str] = None):
        if text:
            self.status_label.configure(text=text)
        self.progress_bar.grid()
        self.progress_bar.start()

    def stop_progress(self, text: Optional[str] = None):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        if text:
            self.status_label.configure(text=text)

    # ---------- GUI BEHAVIOR ----------
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_dir = folder
            self.folder_label.configure(text=f"→ {self.download_dir}")

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def clear_results(self):
        for btn in self.result_buttons:
            btn.destroy()
        self.result_buttons.clear()
        self.subtitles_data.clear()
        self.selected_index.set(-1)

    def on_search_clicked(self):
        title = self.movie_entry.get().strip()
        lang = self.lang_option.get()

        if not title:
            messagebox.showwarning("Input error", "Please enter a movie title.")
            return

        self.clear_results()
        self.start_progress("Searching subtitles...")

        try:
            results = search_subtitles(title, lang)
        except Exception as e:
            self.stop_progress("Search failed.")
            messagebox.showerror("Search error", str(e))
            return

        if not results:
            self.stop_progress("No subtitles found.")
            return

        self.subtitles_data = results

        for idx, item in enumerate(results):
            attrs = item.get("attributes", {})
            release = attrs.get("release", "Unknown release")
            lang_code = attrs.get("language", "??")
            year = attrs.get("year") or ""
            downloads = attrs.get("download_count", attrs.get("downloads", 0))
            text = f"{idx+1}. [{lang_code}] {release} ({year}) - {downloads} downloads"
            rb = ctk.CTkRadioButton(
                self.results_box,
                text=text,
                value=idx,
                variable=self.selected_index,
                width=580
            )
            rb.grid(row=idx, column=0, padx=10, pady=2, sticky="w")
            self.result_buttons.append(rb)

        self.stop_progress(f"Found {len(results)} subtitles.")

    def on_download_clicked(self):
        if not self.subtitles_data:
            messagebox.showwarning(
                "No subtitles", "Search and select a subtitle first."
            )
            return

        idx = self.selected_index.get()
        if idx < 0 or idx >= len(self.subtitles_data):
            messagebox.showwarning(
                "No selection", "Please select a subtitle from the list."
            )
            return

        subtitle = self.subtitles_data[idx]
        attrs = subtitle.get("attributes", {})
        files = attrs.get("files", [])
        if not files:
            messagebox.showerror("No file", "No downloadable file found for this subtitle.")
            return

        file_id = files[0].get("file_id")
        if not file_id:
            messagebox.showerror("No file id", "Cannot find file ID to download.")
            return

        self.start_progress("Downloading subtitle...")

        try:
            path = download_subtitle_file(file_id, self.download_dir)
        except Exception as e:
            self.stop_progress("Download failed.")
            messagebox.showerror("Download error", str(e))
            return

        self.stop_progress(f"Downloaded to: {path}")
        messagebox.showinfo("Download complete", f"Subtitle saved as:\n{path}")

    def on_login_clicked(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Login error", "Please enter both username and password.")
            return
        self.start_progress("Logging in...")
        try:
            token = self.login_opensubtitles(username, password)
            global USER_JWT_TOKEN
            USER_JWT_TOKEN = token
            self.jwt_token = token
            self.username = username
            self.password = password
        except Exception as e:
            self.stop_progress("Login failed.")
            messagebox.showerror("Login error", f"Failed to login:\n{e}")
            return
        self.stop_progress("Login successful.")
        messagebox.showinfo("Login", "Login successful! You can now search and download unlimited subtitles.")
        # Hide all login controls after login
        for widget in self.login_controls:
            widget.grid_remove()
        # Enable and show search controls
        for widget in self.search_controls:
            widget.configure(state="normal")
            widget.grid()

    def open_register_url(self):
        import webbrowser
        webbrowser.open("https://www.opensubtitles.com/")

    def login_opensubtitles(self, username, password):
        url = f"{OPENSUBTITLES_API_URL}/login"
        headers = {
            "Api-Key": OPENSUBTITLES_API_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        payload = {"username": username, "password": password}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"Login failed: {resp.text}")
        data = resp.json()
        return data.get("token")


if __name__ == "__main__":
    app = SubtitleDownloaderApp()
    app.mainloop()
