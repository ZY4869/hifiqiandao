# HiFiNi 自动签到

<img src="https://img.shields.io/badge/Python-3.11-blue" /> <img src="https://img.shields.io/badge/Platform-GitHub%20Actions-green" />

一个基于 GitHub Actions 的 HiFiNi 音乐网站自动签到脚本，支持人机验证处理。

## ✨ 特性

- 🤖 **自动签到**：每天自动执行签到任务
- 🛡️ **人机验证**：自动处理网站的人机验证机制
- 🔄 **智能登录**：支持账号密码自动登录和Cookie方式，失败自动切换浏览器模拟登录
- 📊 **签到统计**：记录每日签到、积分统计、月度年度汇总
- 📱 **Telegram通知**：支持推送签到结果到Telegram（含每日一言）
- 🔔 **详细日志**：完整的运行日志，方便排查问题
- 🎯 **手动触发**：支持手动触发签到任务
- 🆓 **完全免费**：基于 GitHub Actions，完全免费

## 📋 使用说明

### 1. Fork 本仓库

点击右上角的 `Fork` 按钮，将本仓库 Fork 到你的账号下。

### 2. 配置登录信息

本脚本支持两种登录方式，推荐使用账号密码方式（更稳定，自动处理 Cookie 失效）。

#### 方式一：账号密码登录（推荐） ⭐

**优势：**
- ✅ Cookie 失效时自动重新登录
- ✅ 无需手动获取和更新 Cookie
- ✅ 更加稳定可靠

**配置方法：**
1. 进入你 Fork 的仓库
2. 点击 `Settings`（设置）
3. 在左侧菜单中找到 `Secrets and variables` → `Actions`
4. 点击 `New repository secret`
5. 添加以下两个 Secrets：
   - **Name**: `HIFINI_USERNAME`
   - **Value**: 你的账号（邮箱/手机号/用户名）
   
   - **Name**: `HIFINI_PASSWORD`
   - **Value**: 你的密码

#### 方式二：使用 Cookie

如果你不想使用账号密码，也可以使用 Cookie 方式。

**获取 Cookie：**

1. 访问 [HiFiNi 网站](https://www.hifiti.com/)
2. 登录你的账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Network`（网络）标签
5. 按 `F5` 刷新页面
6. 点击任意一个请求，查看 `Request Headers`（请求头）
7. 找到 `Cookie` 字段，复制整个 Cookie 值

**配置方法：**
1. 进入仓库的 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加：
   - **Name**: `HIFINI_COOKIE`
   - **Value**: 粘贴你获取的 Cookie

### 3. 配置 Telegram 通知（可选）

如果你想接收签到结果的 Telegram 通知：

**步骤 1：创建 Telegram Bot**

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令创建新机器人
3. 按提示设置机器人名称和用户名
4. 获得 `Bot Token`，类似：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

**步骤 2：获取 Chat ID**

1. 在 Telegram 中搜索 `@userinfobot`
2. 向它发送任意消息
3. 获得你的 `Chat ID`，是一串数字

**步骤 3：配置 GitHub Secrets**

在仓库 `Settings` → `Secrets and variables` → `Actions` 中添加：
- **Name**: `TG_BOT_TOKEN`
- **Value**: 你的 Bot Token

- **Name**: `TG_CHAT_ID`
- **Value**: 你的 Chat ID

**通知效果示例：**

```
✨ HiFiNi音乐磁场每日签到 ✨

📅 日期: 2025年01月15日 (星期三)
🕒 时间: 08:05:23
👤 账号: your@email.com
✅ 状态: 签到成功
🔑 登录方式: 账号密码
💰 积分: +5

📈 积分统计:
  · 01月积分: 75 金币
  · 2025年积分: 75 金币
  · 历史总积分: 150 金币

📊 签到统计:
  · 总计已签到: 30 天
  · 01月已签到: 15/31 天
  · 今日首次签到 🆕

🚀 打卡成功！向着梦想飞奔吧~

📝 每日一言: 音乐是比一切智慧、一切哲学更高的启示。 —— 贝多芬
```

### 4. 启用 GitHub Actions

1. 进入仓库的 `Actions` 标签
2. 如果提示需要启用 Workflows，点击 `I understand my workflows, go ahead and enable them`
3. 在左侧找到 `HiFiNi 自动签到` 工作流
4. 点击 `Enable workflow`（如果需要）

### 5. 测试运行

1. 进入 `Actions` 标签
2. 选择 `HiFiNi 自动签到` 工作流
3. 点击右侧的 `Run workflow` 按钮
4. 点击 `Run workflow` 确认
5. 等待执行完成，查看运行日志

## ⏰ 运行时间

脚本默认配置为：
- **自动运行**：每天北京时间 8:00（UTC 0:00）
- **手动运行**：随时可以在 Actions 页面手动触发

如需修改运行时间，请编辑 `.github/workflows/checkin.yml` 文件中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'  # 修改这里
```

Cron 表达式说明：
- `0 0 * * *` - 每天 UTC 0:00（北京时间 8:00）
- `0 16 * * *` - 每天 UTC 16:00（北京时间 0:00）
- `0 */12 * * *` - 每 12 小时一次

## 📝 查看运行日志

1. 进入仓库的 `Actions` 标签
2. 点击最近的一次运行记录
3. 点击 `checkin` 任务
4. 展开 `执行签到` 步骤查看详细日志

运行日志示例：
```
==================================================
HiFiNi 自动签到脚本
==================================================
📝 Cookie长度: 234
🚀 开始签到...
✅ 人机验证通过，重新签到...
✨签到成功: 签到成功，获得 5 积分

==================================================
签到结果:
状态: ✅ 成功
信息: 签到成功，获得 5 积分
==================================================
```

## 🔧 本地测试

如果你想在本地测试脚本：

```bash
# 克隆仓库
git clone https://github.com/your-username/hifini-checkin.git
cd hifini-checkin

# 安装依赖
pip install -r requirements.txt
```

**方式一：使用账号密码（推荐）**

```bash
# Windows PowerShell
$env:HIFINI_USERNAME="你的账号"
$env:HIFINI_PASSWORD="你的密码"

# Linux/Mac
export HIFINI_USERNAME="你的账号"
export HIFINI_PASSWORD="你的密码"

# 运行脚本
python hifini_checkin.py
```

**方式二：使用 Cookie**

```bash
# Windows PowerShell
$env:HIFINI_COOKIE="你的Cookie"

# Linux/Mac
export HIFINI_COOKIE="你的Cookie"

# 运行脚本
python hifini_checkin.py
```

**启用 Telegram 通知（可选）**

```bash
# Windows PowerShell
$env:TG_BOT_TOKEN="你的Bot Token"
$env:TG_CHAT_ID="你的Chat ID"

# Linux/Mac
export TG_BOT_TOKEN="你的Bot Token"
export TG_CHAT_ID="你的Chat ID"

# 运行脚本
python hifini_checkin.py
```

## ❓ 常见问题

### Q1: 推荐使用账号密码还是 Cookie？

**A:** 强烈推荐使用账号密码方式！
- ✅ Cookie 失效时自动重新登录
- ✅ 无需手动维护 Cookie
- ✅ 更加稳定可靠

### Q2: 账号密码和Cookie安全吗？

**A:** 绝对安全！

**GitHub Secrets 三重保护：**
1. **加密存储** - 所有Secrets（账号、密码、Cookie、Token）都是加密存储
2. **运行时解密** - 只有在Actions运行时才临时解密到环境变量
3. **自动隐藏** - GitHub会自动检测并隐藏日志中的Secrets内容

**代码安全设计：**
- ✅ 只打印Cookie长度，不打印内容：`Cookie 长度: 146`
- ✅ 只打印Cookie键名，不打印值：`['bbs_token', 'bbs_sid']`
- ✅ 不将敏感信息发送到第三方服务器
- ✅ Telegram通知中不包含任何敏感信息

**即使意外打印，GitHub也会保护：**
```
# 代码中如果写：print(f"Cookie: {cookie}")
# 日志中会显示：Cookie: ***
```

**最佳实践：**
- 使用强密码，定期更换
- 定期检查GitHub Actions日志
- 不要在公开场合分享Secrets

### Q3: 为什么签到失败？

**A:** 可能的原因：
1. 账号密码错误（如使用账号密码方式）
2. Cookie 已过期（如使用 Cookie 方式且未配置账号密码）
3. 网站更新了验证机制
4. 网络问题

解决方法：
- 使用账号密码方式（推荐）
- 检查账号密码是否正确
- 查看 Actions 运行日志获取详细错误信息

### Q4: Cookie 过期了怎么办？

**A:** 
- **使用账号密码方式**：脚本会自动重新登录，无需手动处理
- **仅使用 Cookie 方式**：需要手动重新获取 Cookie 并更新 Secret

### Q5: 如何从 Cookie 方式切换到账号密码方式？

**A:** 
1. 进入仓库的 `Settings` → `Secrets and variables` → `Actions`
2. 添加 `HIFINI_USERNAME` 和 `HIFINI_PASSWORD`
3. 可选：删除 `HIFINI_COOKIE`（保留也不影响，会优先使用账号密码）

### Q6: Actions 为什么没有自动运行？

**A:** 
1. 检查是否已启用 Actions
2. 检查工作流文件是否正确
3. GitHub Actions 可能有延迟，最多可能延迟 10-15 分钟
4. Fork 的仓库默认不会自动运行定时任务，需要手动触发一次

### Q7: 如何关闭自动签到？

**A:** 
1. 进入 `Actions` 标签
2. 选择 `HiFiNi 自动签到` 工作流
3. 点击右上角的 `...` 菜单
4. 选择 `Disable workflow`

### Q8: 为什么requests登录失败但浏览器登录成功？

**A:** 
这是正常现象！网站使用JavaScript加密密码（MD5），我们已经处理了这个问题。如果requests登录失败，脚本会自动切换到Selenium浏览器模拟登录，完全自动化，无需担心！

脚本的智能登录策略：
1. 首先尝试 requests 快速登录（效率高）
2. 失败则自动切换 Selenium 浏览器模拟登录（可靠性高）
3. 获取Cookie后用于后续签到

### Q9: 环境变量中的Cookie会自动更新吗？

**A:** 
不会。环境变量在程序运行时是只读的，无法被程序修改。

**工作原理：**
- GitHub Actions 每次运行都是全新环境
- 使用账号密码方式：每次自动登录获取新Cookie
- 使用Cookie方式：需要手动更新过期的Cookie

**建议：**
- ✅ 推荐使用账号密码方式，自动处理Cookie更新
- ⚠️ 纯Cookie方式需要定期手动更新

### Q10: Telegram通知发送失败怎么办？

**A:** 
可能的原因：
1. Bot Token 或 Chat ID 配置错误
2. Bot 没有发送消息的权限
3. 网络连接问题

解决方法：
1. 检查 Token 和 Chat ID 是否正确
2. 确保已经与 Bot 发起过对话（发送 `/start`）
3. 检查 GitHub Actions 的网络连接

## 📜 许可证

MIT License

## 🔒 安全性保证

### 代码透明
- 所有代码开源，可随时审查
- 不包含任何恶意代码
- 不收集用户信息

### 数据安全
- 账号密码仅用于登录HiFiNi官网
- Cookie仅用于维持登录状态
- 所有敏感信息由GitHub加密存储
- 日志中自动隐藏敏感信息

### 隐私保护
- 不发送数据到第三方服务器（除了HiFiNi和可选的Telegram）
- Telegram通知仅包含公开信息（账号名、积分、签到状态）
- 不包含密码、Cookie等敏感信息

### 建议
- 使用独立的强密码
- 定期更换密码
- 定期检查GitHub Actions运行日志
- 发现异常立即停止使用

## ⚠️ 免责声明

本项目仅供学习交流使用，请勿用于商业用途。使用本项目所造成的一切后果由使用者自行承担。

## 🎁 功能特色

### 智能登录系统
- **三层登录策略**：
  1. Requests 快速登录（效率最高）
  2. Selenium 浏览器模拟登录（可靠性最高）
  3. Cookie 令牌方式（便捷）

### 完善的统计系统
- 每日签到记录
- 金币积分统计
- 月度/年度汇总
- 历史总计数据

### 美观的通知推送
- Telegram 精美通知
- 包含每日一言
- 完整统计信息
- 实时签到状态

### 人机验证处理
- 自动识别验证类型
- 智能计算验证参数
- 无需人工干预

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 [Issue](https://github.com/your-username/hifini-checkin/issues)。

---

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

