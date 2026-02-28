# Rubbishit Journal — 部署说明

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置邮箱（编辑 app.py）
找到第 30–35 行，修改邮件配置：

```python
app.config["MAIL_SERVER"]   = "smtp.gmail.com"      # Gmail
# 或 "smtp.qq.com"                                   # QQ邮箱
# 或 "smtp.163.com"                                  # 163邮箱

app.config["MAIL_USERNAME"] = "your_email@gmail.com" # 你的邮箱
app.config["MAIL_PASSWORD"] = "xxxx xxxx xxxx xxxx"  # 应用专用密码（非登录密码）
app.config["MAIL_DEFAULT_SENDER"] = ("Rubbishit Journal", "your_email@gmail.com")
```

### 3. 各邮箱 SMTP 配置

| 邮箱 | MAIL_SERVER | MAIL_PORT | 说明 |
|------|-------------|-----------|------|
| Gmail | smtp.gmail.com | 587 | 需开启「应用专用密码」|
| QQ邮箱 | smtp.qq.com | 587 | 需开启SMTP并获取授权码 |
| 163邮箱 | smtp.163.com | 587 | 需开启SMTP并设置授权码 |
| Outlook | smtp.office365.com | 587 | 直接使用账号密码 |

### 4. 启动服务
```bash
python app.py
```
服务运行在 http://localhost:5000

### 5. 打开网站
用浏览器打开 `rubbishit.html`，注册功能即可使用。

## 功能说明
- ✅ 邮箱注册（分步：填写信息 → 邮件验证码 → 完成）
- ✅ 4位随机数字验证码，10分钟有效
- ✅ 每小时最多发送3次验证码（防刷）
- ✅ 验证码输入框（4格独立输入，自动跳转）
- ✅ 登录 / 登出
- ✅ 用户状态持久化（Session）
