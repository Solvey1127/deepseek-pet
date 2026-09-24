# 屏幕监测（Screen Monitor）

一个轻量、本地的 Android 应用，用于记录手机**亮屏使用时长**和**每个应用的使用时间段**，精度到秒级。

> 适用场景：家长/监护人了解孩子在校期间是否偷偷玩手机。记录过程无感，不打扰正常使用。

## ✨ 功能特性

- **亮屏统计**：精确记录每次亮屏/息屏的时间点与持续时长
- **秒级时间线**：几点几分打开了哪个应用、用了多久、几点切走，一目了然
- **智能过滤**：只有应用真正处于前台才记为"使用"，锁屏亮着、误触亮屏自动忽略
- **今日概览**：今日亮屏总时长 + 应用使用排行（带比例条）
- **历史统计**：按天汇总，每天亮屏时长、使用应用数
- **一键导出**：生成当日文字报告 / CSV 明细，通过微信等应用转发，实现"远程查看"
- **本地存储**：数据只保存在手机本机数据库，不联网、不上传，隐私安全
- **无感运行**：无通知栏、无悬浮窗，不干扰手机正常使用

## 📱 安装方法

1. 将 `ScreenMonitor-v1.0.apk` 发送到目标手机（微信/QQ 均可）
2. 点击 APK 文件，允许"安装未知来源应用"，完成安装
3. 打开应用，按引导进入系统设置，为本应用打开**「允许访问使用情况」**开关
4. 返回应用即开始自动记录

> 需要 Android 8.0（API 26）及以上系统。

## 🛠 技术栈

| 部分 | 技术 |
|---|---|
| 语言 | Kotlin |
| UI | Jetpack Compose（Material 3） |
| 数据库 | Room（本地 SQLite） |
| 数据源 | Android 系统 `UsageStatsManager`（官方「使用情况访问」机制） |
| 构建 | Gradle 8.10.2 + AGP 8.7.3 + JDK 17 |

## 📂 项目结构

```
app/src/main/java/com/screenmonitor/app/
├── data/
│   ├── Entities.kt          # 数据表实体（应用段 / 亮屏段）
│   ├── UsageDao.kt          # Room 查询
│   ├── AppDatabase.kt       # 数据库
│   ├── UsageCollector.kt    # 核心采集器（解析系统使用事件）
│   └── Permissions.kt       # 权限检查与跳转
├── ui/
│   ├── HomeScreen.kt        # 今日概览页
│   ├── TimelineScreen.kt    # 24小时时间线页（Canvas 绘图）
│   ├── HistoryScreen.kt     # 历史统计页
│   ├── SettingsScreen.kt    # 设置与导出页
│   └── ...
└── util/
    ├── TimeUtils.kt         # 时间格式化
    └── ExportUtils.kt       # 报告导出
```

## ⚙️ 构建

```bash
# 需要 JDK 17 + Android SDK 35
gradle assembleDebug
# 产物：app/build/outputs/apk/debug/app-debug.apk
```

## 📝 说明

- 本应用**不读取任何屏幕内容**（无录屏、无无障碍抓取），仅通过系统官方机制读取应用使用统计。
- 「使用情况访问」为系统特殊权限，首次需在系统设置中手动开启。
- 数据最长保留 60 天，采集时自动清理过期数据。
