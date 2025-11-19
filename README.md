# Subtitle Downloader

A modern Python GUI app to search and download movie subtitles from OpenSubtitles.

![App Icon](assets/icon.ico)

---

## Features

- 🔍 Search subtitles by movie title
- 🌐 Language selection (`en`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `ko`, `ja`)
- 🎨 Dark / Light mode toggle
- 📥 Click-to-select results and download
- 📊 Progress bar for search and download
- 👤 Login for unlimited downloads (OpenSubtitles account required)
- 📝 Register button for new users
- 🖼️ Custom app icon

---

## Setup

```
python -m venv venv

# PowerShell
venv\Scripts\Activate.ps1
# or cmd
venv\Scripts\activate

```

# Set your OpenSubtitles API key as an environment variable before running the app:
# PowerShell
$env:OPENSUBTITLES_API_KEY = "your_api_key_here"
# cmd
set OPENSUBTITLES_API_KEY=your_api_key_here
```

---

## Usage

1. **Run the app:**
   ```bash
   python -m src.subtitle_downloader
   ```
2. **Login:** Enter your OpenSubtitles username and password. If you don't have an account, click **Register** to sign up.
3. **Search:** Enter a movie title, select language, and click **Search Subtitles**.
4. **Download:** Select a subtitle from the results and click **Download Selected Subtitle**.
5. **Change theme:** Toggle Dark/Light mode as you prefer.

---

## Icon

You can customize the app icon by replacing `assets/icon.ico` with your own `.ico` file.

---

## Credits

- Developed by [lahirusanjika](https://github.com/lahirusanjika)
- Powered by [OpenSubtitles API](https://opensubtitles.com/)

---

## License

This project is licensed under the MIT License.

---

## Contributing

Pull requests and suggestions are welcome! Feel free to open issues or contribute via GitHub.
# Subtitle-Downloader
A modern Python GUI app to search and download movie subtitles from OpenSubtitles.
