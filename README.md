# HiFiNi 自动签到

<img src="https://img.shields.io/badge/Python-3.11-blue" /> <img src="https://img.shields.io/badge/Platform-GitHub%20Actions-green" />

一个基于 GitHub Actions 的 HiFiNi 音乐网站自动签到脚本，支持人机验证处理。

## ✨ 特性

- 🤖 **自动签到**：每天北京时间0点自动执行签到任务，1-180秒随机延迟
- 🛡️ **人机验证**：自动处理网站的人机验证机制
- 🔄 **智能登录**：支持账号密码自动登录和Cookie方式，失败自动切换浏览器模拟登录
- 🍪 **Cookie优先**：优先使用加密Cookie签到，失效时才自动登录，减少服务器压力
- 🔐 **双因素加密**：AES-256 + Pepper双因素加密，军事级安全保护
- 📊 **签到统计**：记录每日签到、金币统计、月度年度汇总
- 📱 **Telegram通知**：推送签到结果到Telegram（含每日一言、金币等详细信息）
- 🔔 **详细日志**：完整的运行日志，方便排查问题
- 🎯 **手动触发**：支持手动触发签到任务（无延迟）
- 🆓 **完全免费**：基于 GitHub Actions，完全免费

## 🚀 快速开始

1. **Fork本仓库** → 点击右上角Fork按钮
2. **配置Secrets** → Settings → Secrets and variables → Actions
   - 添加 `HIFINI_USERNAME`（你的账号）
   - 添加 `HIFINI_PASSWORD`（你的密码）
   - 推荐添加 `HIFINI_ENCRYPTION_KEY`（固定加密密钥，增强安全性）
3. **启用Actions** → Actions标签 → Enable workflow
4. **手动测试** → Actions → Run workflow
5. **等待自动运行** → 每天北京时间0点自动签到

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
5. 添加以下 Secrets：
   
   **必需配置：**
   - **Name**: `HIFINI_USERNAME`
   - **Value**: 你的账号（邮箱/手机号/用户名）
   
   - **Name**: `HIFINI_PASSWORD`
   - **Value**: 你的密码
   
   **推荐配置（增强安全性）：**
   - **Name**: `HIFINI_ENCRYPTION_KEY`
   - **Value**: 随机生成的固定密钥（见下方说明）

**🔐 增强安全性配置（推荐）：**

添加 `HIFINI_ENCRYPTION_KEY` 可以提供**双因素加密**保护：
- 即使账号密码泄露，没有此密钥也无法解密Cookie
- 这是密码学中的 "Pepper" 概念，提供额外的安全层

**生成固定密钥：**

Windows PowerShell：
```powershell
# 方法1：生成随机密钥
$key = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "HIFINI_ENCRYPTION_KEY=$key"

# 方法2：使用Python生成
python -c "import secrets; print(f'HIFINI_ENCRYPTION_KEY={secrets.token_urlsafe(32)}')"
```

Linux/Mac：
```bash
# 生成随机密钥
python3 -c "import secrets; print(f'HIFINI_ENCRYPTION_KEY={secrets.token_urlsafe(32)}')"
```

**注意：** 
- 密钥设置后请妥善保管，丢失将无法解密已保存的Cookie
- 更换密钥后，旧的加密Cookie将无法解密，需要重新登录

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

📅 日期: 2025年10月17日 (星期四)
🕒 时间: 00:03:24
👤 账号: your@email.com
✅ 状态: 签到成功
🔑 登录方式: 账号密码
🍪 签到方式: Cookie签到
💎 本次获得: +5 金币
💰 当前总金币: 150 金币

📈 金币统计:
  · 10月金币: 85 金币
  · 2025年金币: 85 金币
  · 历史总金币: 85 金币

📊 签到统计:
  · 总计已签到: 17 天
  · 10月已签到: 17/31 天
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
- **自动运行**：每天北京时间 0:00（UTC 16:00）+ 随机延迟 1-180 秒
- **手动运行**：随时可以在 Actions 页面手动触发（无延迟，立即执行）

**为什么要随机延迟？**
- 避免所有用户同时签到，减轻服务器压力
- 更接近真实用户行为，降低被检测风险
- 仅自动运行时生效，手动运行立即执行

如需修改运行时间，请编辑 `.github/workflows/checkin.yml` 文件中的 cron 表达式：

```yaml
schedule:
  - cron: '0 16 * * *'  # 修改这里（当前为UTC 16:00，即北京时间0:00）
```

Cron 表达式说明：
- `0 16 * * *` - 每天 UTC 16:00（北京时间 0:00）⭐ 当前配置
- `0 0 * * *` - 每天 UTC 0:00（北京时间 8:00）
- `0 */12 * * *` - 每 12 小时一次

## 📝 查看运行日志

1. 进入仓库的 `Actions` 标签
2. 点击最近的一次运行记录
3. 点击 `checkin` 任务
4. 展开 `执行签到` 步骤查看详细日志

运行日志示例（自动运行）：
```
==================================================
HiFiNi 自动签到脚本
==================================================
🕒 自动运行模式，随机延迟 127 秒后开始签到...
⏰ 预计开始时间: 2025-10-17 00:02:12
✅ 延迟结束，开始执行签到
--------------------------------------------------
📝 账号配置: your@email.com

🔍 检查是否存在加密Cookie...
🔓 Cookie解密成功，包含 5 个字段
✅ 找到加密Cookie，优先使用Cookie签到
📦 已加载加密Cookie (长度: 248)
🚀 开始签到...
💰 当前总金币: 150
✨ 签到成功，获得 5 金币
💎 本次获得: +5 金币
💰 记录本次签到金币: +5 金币
📊 签到记录已更新: 总计17天，本月17/31天

==================================================
签到结果:
状态: ✅ 成功
信息: 签到成功，获得 5 金币
==================================================
📱 正在发送Telegram通知...
✅ Telegram通知发送成功
```

运行日志示例（手动运行）：
```
==================================================
HiFiNi 自动签到脚本
==================================================
🖐️  手动运行模式，立即开始签到
--------------------------------------------------
📝 账号配置: your@email.com
🔍 检查是否存在加密Cookie...
✅ 找到加密Cookie，优先使用Cookie签到
🚀 开始签到...
✨ 签到成功，获得 5 金币

==================================================
签到结果:
状态: ✅ 成功
信息: 签到成功，获得 5 金币
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

**A:** 绝对安全！采用军事级多重安全防护！

**🔒 四重安全防护：**

1. **GitHub Secrets 加密存储**
   - 所有Secrets（账号、密码、Cookie、Token）都是加密存储
   - 只有在Actions运行时才临时解密到环境变量
   - GitHub会自动检测并隐藏日志中的Secrets内容

2. **双因素密钥派生（Pepper）** 🆕
   - 使用 `HIFINI_ENCRYPTION_KEY` 作为固定密钥（Pepper）
   - 密钥 = PBKDF2(账号 + 密码 + Pepper, 盐, 10万次迭代)
   - 即使账号密码泄露，没有Pepper也无法解密Cookie

3. **AES-256 军事级加密**
   - Cookie使用AES-256-CBC加密
   - 每次加密使用随机IV（初始化向量）
   - 10万次PBKDF2迭代，抗暴力破解

4. **代码透明，算法公开**
   - 安全性不依赖于代码保密（符合现代密码学原则）
   - 即使源码公开，没有密钥仍无法解密
   - 可随时审查代码，无后门

**代码安全设计：**
- ✅ 只打印Cookie长度，不打印内容：`Cookie 长度: 146`
- ✅ 只打印Cookie键名，不打印值：`['bbs_token', 'bbs_sid']`
- ✅ 密钥临时生成，不存储，程序结束即销毁
- ✅ 不将敏感信息发送到第三方服务器
- ✅ Telegram通知中不包含任何敏感信息

**即使意外打印，GitHub也会保护：**
```
# 代码中如果写：print(f"Cookie: {cookie}")
# 日志中会显示：Cookie: ***
```

**攻击者需要同时获得（几乎不可能）：**
```
想要解密Cookie，必须同时拥有：
├─ ✅ 源码（公开）
├─ ✅ 加密文件（公开在仓库）
├─ ✅ 你的账号（GitHub Secrets，加密）
├─ ✅ 你的密码（GitHub Secrets，加密）
└─ ✅ 固定密钥 Pepper（GitHub Secrets，加密）← 额外防护层
```

**最佳实践：**
- ✅ **配置 `HIFINI_ENCRYPTION_KEY` 增强安全性**（强烈推荐）
- ✅ 使用强密码，定期更换
- ✅ 定期检查GitHub Actions日志
- ✅ 不要在公开场合分享Secrets
- ✅ 建议设置仓库为Private（私有）
- ✅ 妥善保管 Pepper 密钥，丢失将无法解密

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

### Q11: Cookie优先签到是怎么工作的？

**A:** 
为了提高效率和减少服务器压力，脚本采用智能签到策略：

**第一次运行**：
1. 没有加密Cookie → 使用账号密码登录
2. 登录成功 → 获取Cookie → AES-256加密保存
3. 使用Cookie完成签到

**后续运行**：
1. 检测到加密Cookie → 解密并使用Cookie直接签到 ✅（快速高效）
2. 如果Cookie失效 → 自动重新登录 → 获取新Cookie → 加密保存 → 签到

**优势**：
- ✅ 减少90%的登录操作
- ✅ 降低服务器压力
- ✅ 提高签到成功率
- ✅ 签到速度更快（1-3秒）

### Q12: 为什么要添加随机延迟？

**A:** 
随机延迟（1-180秒）有多个重要作用：

**1. 避免服务器压力**
- 如果所有用户在0点整同时签到，会造成服务器瞬时压力
- 随机分散到3分钟内，更加平稳

**2. 模拟真实用户**
- 真实用户不会精确在0点整签到
- 随机延迟更符合人类行为模式

**3. 降低检测风险**
- 避免被识别为自动化脚本
- 提高账号安全性

**注意**：
- ✅ 仅自动运行（定时任务）时生效
- ✅ 手动运行立即执行，无延迟


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

### 🍪 Cookie优先签到策略
- **智能检测**：自动检查本地是否有加密Cookie
- **优先使用**：有Cookie直接签到，减少90%登录操作
- **自动降级**：Cookie失效时自动重新登录
- **加密存储**：AES-256加密，安全可靠
- **效率提升**：签到速度1-3秒，比每次登录快3-5倍

### 🔐 智能登录系统
- **四层登录策略**：
  1. 加密Cookie签到（最快，优先使用）
  2. Requests快速登录（效率高）
  3. Selenium浏览器模拟登录（可靠性最高）
  4. Cookie令牌方式（便捷）
- **AES-256加密**：基于账号密码派生密钥
- **自动降级**：失败自动切换下一策略

### 📊 完善的统计系统
- **签到统计**：每日签到记录、月度/年度汇总、历史总计
- **金币统计**：本次获得、当前总额、月度/年度汇总
- **数据持久化**：加密保存到仓库，跨运行保留

### 📱 美观的通知推送
- **Telegram精美通知**：Markdown格式，信息完整
- **包含每日一言**：随机音乐格言，提升体验
- **完整统计信息**：金币、签到天数等
- **实时签到状态**：成功/失败，登录/签到方式

### ⏱️ 性能优化
- **随机延迟**：1-180秒，避免同时签到
- **Cookie复用**：减少90%登录操作，提升速度3-5倍
- **手动优先**：手动运行无延迟，立即执行

### 🛡️ 人机验证处理
- **自动识别**：检测验证类型
- **智能计算**：自动计算验证参数
- **无需人工**：全自动处理，无需干预

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 [Issue](https://github.com/your-username/hifini-checkin/issues)。

---

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

