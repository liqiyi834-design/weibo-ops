# Telegram 消息拉取

当前只保留“拉取消息”能力：

- 不监听
- 不主动发送
- 不推送文件
- 不自动回复

## 设置 Token

把 Bot Token 复制到剪贴板后，在 PowerShell 里运行：

```powershell
$env:TELEGRAM_BOT_TOKEN = (Get-Clipboard).Trim()
```

## 拉取消息

```powershell
cd D:\微博
powershell -ExecutionPolicy Bypass -File .\tools\Telegram-Inbox.ps1
```

消息会保存到：

```text
D:\微博\data\telegram_inbox.csv
```

## 注意

Token 不要发到聊天里，也不要截图。
