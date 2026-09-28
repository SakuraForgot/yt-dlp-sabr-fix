# yt-dlp SABR Test Core

临时、非官方的 Windows x64 SABR 测试核心。直接构建 [yt-dlp PR #13515](https://github.com/yt-dlp/yt-dlp/pull/13515) 作者的 [feat/youtube/sabr](https://github.com/coletdjnz/yt-dlp-dev/tree/feat/youtube/sabr) 分支，不重新实现 SABR，不手动摘取提交。

**[下载预发布版本](https://github.com/SakuraForgot/yt-dlp-sabr-fix/releases)** · [自动构建](https://github.com/SakuraForgot/yt-dlp-sabr-fix/actions/workflows/build.yml)

## 自动构建

- 每 6 小时检查一次上游，另支持手动触发与构建脚本变更触发；GitHub 调度可能延迟，长期无活动的公开仓库可能被暂停调度。
- 每次先解析分支为完整 SHA，再按该 SHA 检出。上游 SHA 与构建配方均未改变时跳过已发布构建。
- 手动输入完整 `source_sha` 可重建指定 revision；`force_rebuild` 生成独立版本，不覆盖历史发布资产。
- 使用 Python 3.12.12 x64、上游带哈希依赖锁、lazy extractors 与官方 `python -m bundle.pyinstaller --clean`。不维护自制 spec。
- CI 运行上游 SABR 测试，检查 PE x64、打包模块、无 Python/PATH 环境下独立启动。构建与发布分 job，只有发布 job 有写权限。
- 输出 `yt-dlp.exe`、`BUILD_INFO.json`、`VALIDATION.json`、`SHA256SUMS.txt`、准确上游源代码快照及许可证。完整提交、配方哈希、构建时间、Python/依赖、显示版本可追溯。

单 EXE 不要求用户安装 Python 或 Python 包；YouTube 所需 JS runtime、POT Provider 与媒体合并所需 FFmpeg 仍由调用方提供。此分支使用 protobug；CI 检查其实际被收集，不能把未使用的 protobuf 当作缺失依赖。

## 自构建

Windows x64 安装 Git 和 [uv](https://docs.astral.sh/uv/)，克隆本仓库后运行（uv 提供确切的 Python 3.12.12）：

```powershell
uv python install 3.12.12
uv venv --python 3.12.12 --seed .venv
.venv/Scripts/python.exe scripts/resolve.py
$source = Get-Content resolved.json | ConvertFrom-Json
git clone --branch $source.branch "https://github.com/$($source.repository).git" upstream
git -C upstream checkout --detach $source.source_sha
.venv/Scripts/python.exe scripts/build.py
```

产物位于 `dist/`。建议在独立构建机操作。手动指定 revision 时在解析前设置 `$env:SOURCE_SHA` 为完整 SHA。

## 在线验证与 FluentYTDL

CI 成功只代表 `VALIDATION.json` 中明确通过的项目。GitHub 构建机不会使用用户 Cookie 或 POT Token；在线 SABR 下载、合并、播放与 FluentYTDL 验收必须另行记录对应 EXE 哈希。

```powershell
.\yt-dlp.exe --version
.\yt-dlp.exe --help
.\yt-dlp.exe -v "https://www.youtube.com/watch?v=jNQXAC9IVRw"
.\yt-dlp.exe --extractor-args "youtube:formats=duplicate" -F "https://www.youtube.com/watch?v=jNQXAC9IVRw"
.\yt-dlp.exe --extractor-args "youtube:formats=duplicate" -f "ba[protocol=sabr]+bv[protocol=sabr]" --merge-output-format mkv "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

格式 JSON 中的 `protocol=sabr`、实际音视频下载、FFmpeg 合并与播放均需核实。POT、Deno、代理与 FFmpeg 参数继续采用宿主应用的现有设置。

FluentYTDL 继续使用现有 `yt-dlp.exe` 文件名和 CLI。**本仓库不包含 FluentYTDL 源码或补丁。** 适配边界与操作步骤见 [兼容性说明](docs/FLUENTYTDL.md)。

## 更新与许可

EXE 自身的 `-U` 已禁用，更新请下载本仓库的新资产。这不能阻止宿主程序的更新、重装或修复操作覆盖 EXE。

上游代码与二进制的许可证以随附 `LICENSE`、`THIRD_PARTY_LICENSES.txt` 为准。本仓库原创构建脚本采用 MIT；项目与 yt-dlp 官方团队、SABR PR 作者不存在官方发布关系。
