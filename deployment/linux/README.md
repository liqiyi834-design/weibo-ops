# Linux 云服务器部署

目标：单台 Ubuntu 服务器运行 HotComment-AI、Streamlit UI、Hermes gateway/cron 和本地 MCP。

默认路径：

```text
/opt/weibo-ops
```

默认运行用户：

```text
weiboops
```

## 1. 系统依赖

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx curl
```

## 2. 创建运行用户

```bash
sudo useradd -m -s /bin/bash weiboops || true
sudo mkdir -p /opt/weibo-ops
sudo chown -R weiboops:weiboops /opt/weibo-ops
```

## 3. 拉取项目

```bash
sudo -iu weiboops
git clone https://github.com/liqiyi834-design/weibo-ops.git /opt/weibo-ops
cd /opt/weibo-ops
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

至少配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-flash
USE_OPENAI_EMBEDDINGS=false
API_BASE_URL=http://127.0.0.1:8000
WEIBO_COOKIE=
```

## 4. 本地验证

```bash
cd /opt/weibo-ops
source .venv/bin/activate
python -m pytest tests -q -p no:cacheprovider
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开窗口：

```bash
curl http://127.0.0.1:8000/health
```

## 5. 安装 systemd 服务

退出到有 sudo 权限的用户：

```bash
sudo cp /opt/weibo-ops/deployment/linux/systemd/weibo-ops-fastapi.service /etc/systemd/system/
sudo cp /opt/weibo-ops/deployment/linux/systemd/weibo-ops-streamlit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now weibo-ops-fastapi
sudo systemctl enable --now weibo-ops-streamlit
```

查看日志：

```bash
sudo journalctl -u weibo-ops-fastapi -f
sudo journalctl -u weibo-ops-streamlit -f
```

## 6. Nginx

复制配置并替换域名：

```bash
sudo cp /opt/weibo-ops/deployment/linux/nginx/weibo-ops.conf /etc/nginx/sites-available/weibo-ops.conf
sudo nano /etc/nginx/sites-available/weibo-ops.conf
sudo ln -sf /etc/nginx/sites-available/weibo-ops.conf /etc/nginx/sites-enabled/weibo-ops.conf
sudo nginx -t
sudo systemctl reload nginx
```

需要 HTTPS 时安装 certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

## 7. Hermes 和 MCP

在 `weiboops` 用户下安装 Hermes：

```bash
sudo -iu weiboops
cd /opt/weibo-ops
# 按 Hermes 官方 Linux 安装方式安装 hermes CLI
```

生成本机 MCP 配置片段：

```bash
cd /opt/weibo-ops
bash tools/new_hermes_mcp_config.sh --python /opt/weibo-ops/.venv/bin/python
cat configs/hermes.mcp.local.yaml
```

把生成的 `mcp_servers.hotcomment_ai` 段落加入：

```bash
nano ~/.hermes/config.yaml
```

验证：

```bash
hermes mcp list
hermes mcp test hotcomment_ai
bash tools/invoke_hermes_workflow.sh --workflow auto_candidate_to_review_text --dry-run
```

## 8. Hermes gateway/cron

配置好 Telegram、Email、企业微信等推送通道后：

```bash
sudo cp /opt/weibo-ops/deployment/linux/systemd/hermes-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-gateway
sudo journalctl -u hermes-gateway -f
```

示例定时任务：

```bash
hermes cron create "30 8 * * *" "读取 configs/hermes.workflows/auto_candidate_to_review_text.md，并按其中步骤执行，最后发给我过目。" --name "hotcomment-morning-0830" --deliver telegram --workdir "/opt/weibo-ops"
```

## 9. 更新

```bash
sudo -iu weiboops
cd /opt/weibo-ops
git status --short --branch
git pull --ff-only origin main
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q -p no:cacheprovider
sudo systemctl restart weibo-ops-fastapi weibo-ops-streamlit hermes-gateway
```

### Git 更新边界

服务器只作为部署工作树，默认不在服务器生成新提交。

推荐路径：

```text
本机 commit/push
-> 服务器 git pull --ff-only
-> 测试
-> 重启服务
```

如果服务器访问 GitHub 不稳定，优先在本机生成文件、patch 或 bundle 后上传；服务器只同步到本机/GitHub 已存在的提交。不要在服务器上随手 `git commit` 或 `git am` 制造同内容不同 hash 的本地提交。

服务器出现本地改动时：

```bash
git status --short --branch
git diff > /tmp/weibo-ops-server.diff
```

先确认这些改动是否需要移植回本机，再执行覆盖、reset 或重新部署。不要在未备份 diff 的情况下清理工作树。

## 10. 备份

至少备份：

```text
/opt/weibo-ops/.env
/opt/weibo-ops/output/
/opt/weibo-ops/app/knowledge/inbox/
/opt/weibo-ops/.rag_index/
/home/weiboops/.hermes/
```
