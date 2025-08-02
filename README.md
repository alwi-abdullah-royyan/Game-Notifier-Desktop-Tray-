# 🎮 Game Notifier (Desktop Tray)

A Python tray notifier that monitors a website's API and notifies you via system tray + Windows toast when new games or content are uploaded.

> ⚠️ This project does **not** include private API keys or endpoints. You must configure it yourself.

---

## 🧰 Features

- ✅ Background checker for new uploads
- 🔔 Toast + tray icon notifications
- 📁 Rotating logs + automatic compression
- 📊 Log reader & upload frequency analyzer
- ❌ Auto-retries on failure with timeout

---

## 🖼 Tray Menu

- `New games: N` → shows how many missed
- `Read log` → opens the latest log
- `Clear notification` → resets count + clears log files
- `Read update/upload pattern` → shows time histogram
- `Quit` → clean shutdown

---

## 🚀 Setup

1. 🔧 Copy `config_example.json` to `config.json`
2. Fill in your API URL and icon path.
3. Make sure required packages are installed:

```bash
pip install requests pystray pillow win10toast
````

4. Run it:

```bash
python notifier.py
```

---

## 🔒 Security

This repo **does not** expose:

* Any private API keys
* Real endpoint structure
* Site-specific data

You must configure your own endpoint.

---

## 📜 Logging

* Logs are rotated at 5MB
* Older logs are compressed to `.gz`
* Game alerts are timestamped in `/logs`

---

## 📜 License

MIT – Use it, fork it, modify it. But **don’t abuse API limits** or violate ToS of any service you plug in.

---

## 🗨️ Feedback?

PRs and issues welcome!
