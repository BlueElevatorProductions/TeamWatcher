# TeamWatcher ICS Feed - Hosting Documentation

Complete guide for hosting the TeamWatcher ICS calendar feed service on macOS with Caddy HTTPS reverse proxy.

## Table of Contents
- [Initial Setup](#initial-setup)
- [Local Development](#local-development)
- [Production Service (launchd)](#production-service-launchd)
- [HTTPS with Caddy](#https-with-caddy)
- [Testing](#testing)
- [Calendar Subscription](#calendar-subscription)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Initial Setup

### 1. Extract and Install Dependencies

```bash
# Navigate to project directory
cd ~/Development/ClaudeAccess/TeamWatcher

# Extract the ZIP file (if not already done)
unzip -q teamwatcher_feed.zip

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi==0.115.5` - Web framework
- `uvicorn[standard]==0.32.0` - ASGI server
- `pytz==2024.1` - Timezone support

### 2. Initialize Git Repository

```bash
# Initialize git repo
git init

# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: TeamWatcher ICS feed service"

# Create GitHub repository and push
gh repo create BlueElevatorProductions/TeamWatcher --public --source=. --remote=origin --push
```

**Repository:** https://github.com/BlueElevatorProductions/TeamWatcher

---

## Local Development

### Start Development Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start uvicorn with auto-reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Server will be available at: `http://127.0.0.1:8000`

### Test Endpoints

```bash
# Health check
curl http://127.0.0.1:8000/health

# Bills ICS feed (with parameters)
curl http://127.0.0.1:8000/ics/bills?zip=11218&subs=paramount,youtubetv

# UNC Men's Basketball ICS feed
curl http://127.0.0.1:8000/ics/unc

# Check headers
curl -i http://127.0.0.1:8000/ics/bills?zip=11218&subs=paramount,youtubetv | head -10
```

**Expected response headers:**
- `HTTP/1.1 200 OK`
- `Content-Type: text/calendar; charset=utf-8`
- Body starts with `BEGIN:VCALENDAR`

---

## Production Service (launchd)

### 1. Create Log Directory

```bash
mkdir -p ~/Library/Logs/teamwatcher_api
```

### 2. LaunchAgent Configuration

File: `~/Library/LaunchAgents/com.teamwatcher.api.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.teamwatcher.api</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/chrismcleod/Development/ClaudeAccess/TeamWatcher/.venv/bin/uvicorn</string>
        <string>app.main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/chrismcleod/Development/ClaudeAccess/TeamWatcher</string>

    <key>StandardOutPath</key>
    <string>/Users/chrismcleod/Library/Logs/teamwatcher_api/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/chrismcleod/Library/Logs/teamwatcher_api/stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/chrismcleod/Development/ClaudeAccess/TeamWatcher/.venv/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

### 3. Load and Manage Service

```bash
# Load the service (starts immediately and on login)
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist

# Verify service is running
launchctl list | grep teamwatcher

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist

# Restart the service
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist

# View real-time logs
tail -f ~/Library/Logs/teamwatcher_api/stderr.log
```

### 4. Verify Service

```bash
# Check if service is running
launchctl list | grep teamwatcher

# Expected output: PID  StatusCode  Label
# Example: 37390  0  com.teamwatcher.api

# Test endpoint
curl -s http://127.0.0.1:8000/ics/bills | head -5

# View logs
tail -20 ~/Library/Logs/teamwatcher_api/stderr.log
```

---

## HTTPS with Caddy

### 1. Install Caddy

```bash
# Install via Homebrew
brew install caddy

# Verify installation
caddy version
```

### 2. Caddyfile Configuration

File: `~/Development/ClaudeAccess/TeamWatcher/Caddyfile`

```caddy
# Replace feed.example.com with your actual domain

feed.example.com {
    # Automatic HTTPS with Let's Encrypt
    reverse_proxy 127.0.0.1:8000

    # Enable gzip compression
    encode gzip

    # Security headers
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Access logging
    log {
        output file /opt/homebrew/var/log/caddy/teamwatcher_access.log
        format json
    }
}

# Optional: redirect www to non-www
www.feed.example.com {
    redir https://feed.example.com{uri} permanent
}
```

### 3. DNS Configuration

**Before starting Caddy, configure your DNS:**

1. Log into your DNS provider
2. Create an A record pointing to your public IP:
   ```
   Type: A
   Name: feed (or your chosen subdomain)
   Value: <YOUR_PUBLIC_IP>
   TTL: 3600
   ```
3. Optional: Create AAAA record for IPv6
4. Wait for DNS propagation (1-5 minutes typically)

**Find your public IP:**
```bash
curl -4 ifconfig.me
```

### 4. Start Caddy

```bash
# Create Caddy log directory
mkdir -p /opt/homebrew/var/log/caddy

# Validate Caddyfile syntax
caddy validate --config ~/Development/ClaudeAccess/TeamWatcher/Caddyfile

# Start Caddy in foreground (for testing)
caddy run --config ~/Development/ClaudeAccess/TeamWatcher/Caddyfile

# Or start as background service
caddy start --config ~/Development/ClaudeAccess/TeamWatcher/Caddyfile
```

### 5. Start Caddy on Login (via Homebrew Services)

```bash
# First, update the default Caddyfile location
sudo mkdir -p /opt/homebrew/etc
sudo cp ~/Development/ClaudeAccess/TeamWatcher/Caddyfile /opt/homebrew/etc/Caddyfile

# Start Caddy and enable on login
brew services start caddy

# Check status
brew services info caddy

# View logs
tail -f /opt/homebrew/var/log/caddy/teamwatcher_access.log
```

### 6. Verify Let's Encrypt Certificate

```bash
# Check certificate details
curl -vI https://feed.example.com 2>&1 | grep -E 'SSL|issuer'

# Or use openssl
echo | openssl s_client -connect feed.example.com:443 2>/dev/null | openssl x509 -noout -text | grep -E 'Issuer|Subject|Not'
```

---

## Testing

### Local Testing (without HTTPS)

```bash
# Test Bills endpoint with parameters
curl -i "http://127.0.0.1:8000/ics/bills?zip=11218&subs=paramount,youtubetv"

# Test UNC endpoint
curl -i "http://127.0.0.1:8000/ics/unc"

# Save to file for inspection
curl -o bills.ics "http://127.0.0.1:8000/ics/bills?zip=11218&subs=paramount,youtubetv"
open bills.ics  # Opens in default calendar app
```

### Production Testing (with HTTPS)

```bash
# Replace feed.example.com with your actual domain

# Test Bills endpoint
curl -i "https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv"

# Test UNC endpoint
curl -i "https://feed.example.com/ics/unc"

# Verify Content-Type header
curl -I "https://feed.example.com/ics/bills" 2>&1 | grep -i content-type

# Expected: Content-Type: text/calendar; charset=utf-8
```

### Verify ICS Format

```bash
# Check that response starts with valid ICS structure
curl -s "https://feed.example.com/ics/bills" | head -15

# Expected output:
# BEGIN:VCALENDAR
# VERSION:2.0
# PRODID:-//TeamWatcher//Bills — 11218//EN
# CALSCALE:GREGORIAN
# METHOD:PUBLISH
# ...
```

---

## Calendar Subscription

### Subscription URLs

**Buffalo Bills (with ZIP code and subscriptions):**
```
https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv
```

**UNC Men's Basketball:**
```
https://feed.example.com/ics/unc
```

### Subscribe from Apple Calendar (iOS/macOS)

**iOS:**
1. Open **Settings** app
2. Tap **Calendar** → **Accounts** → **Add Account**
3. Tap **Other** → **Add Subscribed Calendar**
4. Enter URL: `https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv`
5. Tap **Next** → **Save**

**macOS:**
1. Open **Calendar** app
2. **File** → **New Calendar Subscription**
3. Enter URL: `https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv`
4. Click **Subscribe**
5. Configure auto-refresh (recommended: Every hour or Every day)

### Subscribe from Google Calendar

1. Open [Google Calendar](https://calendar.google.com)
2. Click **+** next to "Other calendars"
3. Select **From URL**
4. Paste URL: `https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv`
5. Click **Add calendar**

**Note:** Google Calendar refreshes subscribed calendars approximately every 24 hours.

### Subscribe from Outlook

1. Open Outlook (web or desktop)
2. Go to **Calendar**
3. Click **Add calendar** → **Subscribe from web**
4. Paste URL: `https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv`
5. Name the calendar and click **Import**

---

## Troubleshooting

### Service Won't Start

**Check if port 8000 is in use:**
```bash
lsof -i :8000
# Kill process if needed: kill -9 <PID>
```

**Check launchd service status:**
```bash
launchctl list | grep teamwatcher
# If exit code is non-zero, check logs
```

**View error logs:**
```bash
tail -50 ~/Library/Logs/teamwatcher_api/stderr.log
```

**Common issues:**
- Virtual environment path is incorrect in plist
- Working directory doesn't exist
- Python dependencies not installed
- Port 8000 already in use

### Caddy Certificate Issues

**Port 80/443 already in use:**
```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
brew services stop nginx  # if nginx is running
```

**DNS not propagating:**
```bash
# Check DNS resolution
dig feed.example.com
nslookup feed.example.com

# Wait 5-10 minutes for DNS to propagate
```

**Certificate not being issued:**
```bash
# Check Caddy logs
tail -f /opt/homebrew/var/log/caddy/teamwatcher_access.log

# Ensure firewall allows ports 80 and 443
# Ensure your router forwards ports 80 and 443 to your Mac
```

### Calendar Not Updating

**Check refresh interval:**
- Apple Calendar: Typically refreshes every hour
- Google Calendar: Refreshes approximately every 24 hours
- Force refresh in Apple Calendar: Right-click calendar → **Refresh**

**Verify endpoint is accessible:**
```bash
curl -I "https://feed.example.com/ics/bills"
# Should return HTTP 200 OK
```

### API Returns Wrong Data

**Check logs for errors:**
```bash
tail -f ~/Library/Logs/teamwatcher_api/stderr.log
```

**Restart the service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist
```

**Test locally first:**
```bash
# Stop launchd service
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist

# Run manually with debug output
cd ~/Development/ClaudeAccess/TeamWatcher
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### View All Logs

```bash
# uvicorn service logs
tail -f ~/Library/Logs/teamwatcher_api/stderr.log

# Caddy access logs
tail -f /opt/homebrew/var/log/caddy/teamwatcher_access.log

# System logs for launchd
log stream --predicate 'subsystem == "com.apple.launchd"' --level debug | grep teamwatcher
```

---

## Maintenance

### Update Dependencies

```bash
cd ~/Development/ClaudeAccess/TeamWatcher
source .venv/bin/activate

# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all packages (be cautious)
pip install --upgrade -r requirements.txt

# Restart service after updates
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist
```

### Update Game Data

Edit the data files to add new games or update existing ones:
- `app/data_bills_2025.py` - Buffalo Bills schedule
- `app/data_unc_2025.py` - UNC Men's Basketball schedule

After updating, restart the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist
```

### Update Caddy

```bash
# Update Caddy via Homebrew
brew upgrade caddy

# Restart Caddy service
brew services restart caddy
```

### Backup Configuration

```bash
# Backup launchd plist
cp ~/Library/LaunchAgents/com.teamwatcher.api.plist ~/Desktop/com.teamwatcher.api.plist.backup

# Backup Caddyfile
cp /opt/homebrew/etc/Caddyfile ~/Desktop/Caddyfile.backup

# Or commit to git
cd ~/Development/ClaudeAccess/TeamWatcher
git add .
git commit -m "Update configuration"
git push
```

### Monitor Service Health

```bash
# Check if service is running
launchctl list | grep teamwatcher

# Check process
ps aux | grep uvicorn

# Test endpoint
curl -I http://127.0.0.1:8000/health

# Monitor logs
tail -f ~/Library/Logs/teamwatcher_api/stderr.log
```

### Rotate Logs

```bash
# Create log rotation script
cat > ~/Development/ClaudeAccess/TeamWatcher/rotate_logs.sh << 'EOF'
#!/bin/bash
LOG_DIR=~/Library/Logs/teamwatcher_api
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Archive old logs
if [ -f "$LOG_DIR/stderr.log" ]; then
    mv "$LOG_DIR/stderr.log" "$LOG_DIR/stderr_$TIMESTAMP.log"
    gzip "$LOG_DIR/stderr_$TIMESTAMP.log"
fi

if [ -f "$LOG_DIR/stdout.log" ]; then
    mv "$LOG_DIR/stdout.log" "$LOG_DIR/stdout_$TIMESTAMP.log"
    gzip "$LOG_DIR/stdout_$TIMESTAMP.log"
fi

# Delete logs older than 30 days
find "$LOG_DIR" -name "*.log.gz" -mtime +30 -delete

# Restart service to create new log files
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist
EOF

chmod +x ~/Development/ClaudeAccess/TeamWatcher/rotate_logs.sh

# Run manually or add to cron
# To add to cron: crontab -e
# Add line: 0 0 * * 0 ~/Development/ClaudeAccess/TeamWatcher/rotate_logs.sh
```

---

## Quick Reference

### Essential Commands

```bash
# Start service
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist

# Restart service
launchctl unload ~/Library/LaunchAgents/com.teamwatcher.api.plist && \
launchctl load ~/Library/LaunchAgents/com.teamwatcher.api.plist

# View logs
tail -f ~/Library/Logs/teamwatcher_api/stderr.log

# Test local endpoint
curl http://127.0.0.1:8000/ics/bills?zip=11218&subs=paramount,youtubetv

# Test production endpoint
curl https://feed.example.com/ics/bills?zip=11218&subs=paramount,youtubetv

# Check Caddy status
brew services list | grep caddy

# Restart Caddy
brew services restart caddy
```

### File Locations

- **Project:** `~/Development/ClaudeAccess/TeamWatcher/`
- **Virtual environment:** `~/Development/ClaudeAccess/TeamWatcher/.venv/`
- **LaunchAgent plist:** `~/Library/LaunchAgents/com.teamwatcher.api.plist`
- **Service logs:** `~/Library/Logs/teamwatcher_api/`
- **Caddyfile:** `/opt/homebrew/etc/Caddyfile`
- **Caddy logs:** `/opt/homebrew/var/log/caddy/`
- **GitHub:** https://github.com/BlueElevatorProductions/TeamWatcher

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs: `~/Library/Logs/teamwatcher_api/stderr.log`
- Test locally before testing in production
- Verify DNS settings if Caddy certificate fails
- Ensure ports 80, 443, and 8000 are not blocked

---

**Setup completed:** 2025-11-09
**Python version:** 3.9.6
**Caddy version:** 2.10.2
**FastAPI version:** 0.115.5
