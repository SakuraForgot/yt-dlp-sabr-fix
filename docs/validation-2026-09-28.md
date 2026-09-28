# 2026-09-28 公开核心验收记录

本记录只对应下列文件，不能推广到自动发布的后续 revision。

| 项目 | 身份 |
| --- | --- |
| Release | [sabr-6ef0ae00f0a4-10a9f1a4961d](https://github.com/SakuraForgot/yt-dlp-sabr-fix/releases/tag/sabr-6ef0ae00f0a4-10a9f1a4961d) |
| 上游分支 | `coletdjnz/yt-dlp-dev` / `feat/youtube/sabr` |
| 上游 SHA | `6ef0ae00f0a4e9dd042193b3f5a2bb28b5fc0ca6` |
| EXE SHA256 | `11d91b1e2ba3695f176aab4ebea42d6af57182f9b5e9ac5923312f31b94379e2` |
| 显示版本 | `2026.09.28` |
| 构建时间 UTC | `2026-09-28T11:48:03.822735+00:00` |
| 平台 | Windows x64 / 单 EXE / Python 3.12.12 |
| 核心构建配方 SHA256 | `10a9f1a4961d389515c434436582d30bdf97044fb973d229a08c81779b3cba2e` |

## 已验证

- [完整 CI](https://github.com/SakuraForgot/yt-dlp-sabr-fix/actions/runs/36417662631)成功：724 项上游 SABR 测试通过；PE x64、空 PATH 单文件启动、`--version` / `--help`、打包 protobug 与 SABR/proto 模块检查通过。
- 公开 Release 下载回读，SHA256SUMS 列出的全部 7 个资产一致。
- [重复触发](https://github.com/SakuraForgot/yt-dlp-sabr-fix/actions/runs/36418096722)成功跳过 build/publish，没有重复发布。
- 公共样例 `https://www.youtube.com/watch?v=jNQXAC9IVRw`：默认下载、`formats=duplicate -F`、强制 SABR 音频+视频均退出 0，未出现 traceback 或缺模块异常。
- 沿用本地 FluentYTDL 测试副本的 POT 插件、bgutil Provider、Deno、FFmpeg；应用原有 CLI 解析得到 30 个 `protocol=sabr` 格式。
- 强制下载得到 Opus 音频与 AV1 视频，FFmpeg 合并为 MKV；ffprobe 双流检查、全文件解码通过。Qt Multimedia 静音播放完整结束，284 帧、19021ms、无播放错误。
- FluentYTDL 源码测试副本的原生执行器下载与 StagingArea 校验/提交通过；其独立合并文件也通过全文件解码。

## 发现并在本地测试副本修复的适配问题

上游 SABR 的并行进度行会带 `1: ` / `2: ` 前缀，即便使用自定义 progress-template。现有 FluentYTDL 解析器要求行首直接是 `FLUENTYTDL|`，因此下载成功但下载进度被忽略，只收到后处理通知。

本地测试副本仅增加对该结构化前缀的识别，保留原始流文件名、字节数和 codec，不改 POT 或下载流程。修复后真实下载收到 22 条下载进度：音频、视频各 11 条，分别为 252182、223779 字节。版本、插件同步、核心更新保护和输出解析相关测试共 48 项通过。

此处只公开问题和验证结果，**不公开 FluentYTDL 源码或补丁**。本次没有重新打包 FluentYTDL，之前的应用测试包不会自动获得这次解析修复，正式版也未修改。

## 尚未完成的应用验收

- GUI 百分比汇总、音视频标签、暂停/恢复/取消、播放列表批量调度尚未作为本次发布的验收结论。收到逐流进度不代表 GUI 汇总语义已完整适配。
- 分段下载、限速、并发分片是上游已声明的功能限制；直播实验功能不在本次测试范围。
- 字幕、封面、VR、多语言选择和账号 SABR-only 回退尚需独立回归。本次样例使用匿名请求，没有使用个人 Cookie。
- 正式版更新/重装/修复仍可能覆盖手动替换的 EXE。EXE 禁用 `-U` 不等于宿主应用已经固定核心。

原始日志和应用文件均仅保存在本地。Release 中的 VALIDATION.json 是 CI 当时的结果，在线测试结果另列于本文，未回写或替换原有发布资产。
