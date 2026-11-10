# OnePlus 6T (fajita) 上跑 iOS：当前状态与下一步

更新时间：2026-11-10（会话记录）

## 已经跑通的部分

| 阶段 | 状态 | 证据 |
|---|---|---|
| UEFI（Mu-Silicium，从 enchilada 派生 fajita 平台） | ✅ | `Build/fajitaPkg/RELEASE_CLANGPDB/FV/SILICIUM_UEFI.fd` = 3,145,728 B；真机出图 |
| UniXNU 菜单 | ✅ | 屏幕显示 `UniXNU version 0.1.0`、`config: \EFI\UniXNU\unixnu.toml`、条目 `fajita first boot` |
| DarwinBoot 交接 | ✅ | `DARWINBOOT: video base=0x9d400000 display=1 row=4320 width=1080 height=2340 depth=32`、`inputs validated` |
| payload 打包与刷写 | ✅ | `payload.img` 201,326,592 B 写入 `system_a`（196,608 KB，OKAY） |
| 内核镜像（console profile） | ✅ | CI 产出 `kernel.macho` 53,977,088 B，sha256 `5b9ea79e…` |
| 内核真正启动 | ❌ | 倒计时后静默复位回 OpenHarmony，无任何内核输出 |

## 现在的两个卡点

### 1. 探针工具不接受这份内核

```
python3 scripts/patch-xnu-entry-probe.py --reset-delay 10 /tmp/probe.macho
Padding at 0xfffffff0073ea500 is not empty
```

工具假定 `_start` 之后有全零 padding 放探针代码，console 内核的段布局不同，该地址被占用，工具按设计拒绝继续。

### 2. 打开 legacy display 会重新引入候选依赖

`CONFIG_XNU_NATIVE_LEGACY_DISPLAY=y` 需要 `build-native-legacy-display.py`，而该脚本要求：

```
FAJITA_DISPLAY_CANDIDATE (or FAJITA_STORAGE_CANDIDATE) must name a prelinked fajita kernel.macho with its kernel.json beside it
```

也就是说：显示 kext 的构建依赖一份「已经 prelink 过的内核」，而 prelink 又排在 archive 之后 —— 与 storage 审计同一个循环。

## 下一步（二阶段构建）

1. **第一阶段**（display 关闭，已验证可行）：构建 console 内核，产出 `kernel.macho` + `kernel.json`，两者一起作为 candidate 保存；
2. **第二阶段**：打开 `NATIVE_LEGACY_DISPLAY`，加回 `build-native-legacy-display.py`，设置
   `FAJITA_DISPLAY_CANDIDATE=/tmp/cand/kernel.macho`，重新构建内核；
3. 用第二阶段的内核打 payload，参数带 `offline-legacy-*` 那组，刷 `system_a`，`fastboot boot`。

预期：`NativeLegacyDisplay` 接管 UEFI framebuffer 后，`-v` 的内核日志会真正画到屏幕上，能看到 `Darwin Kernel Version 23.x` 或 panic 文本。

## 关键命令备忘

```bash
# 构建（GitHub Actions，workflow_dispatch）
gh workflow run kernel.yml --repo stesen/UniXNU-fajita

# 本地：打 payload（用已下载的内核）
./unixnu build payload -D ../device-console --kernel <kernel.macho> --unique-chip-id 0badc0de

# 刷写与启动
fastboot set_active b
fastboot flash system_a out/fajita/payload/payload.img
fastboot boot out/fajita/boot/boot.img
```

## 设备事实（实测）

```
model      OnePlus 6T (fajita)，product sdm845，serial d4073581
bootloader unlocked=yes，current-slot=b，slot-retry b 偏低
boot_a/b   64 MiB ×2 ；system_a/b 2.79 GiB ×2 ；userdata 110 GiB f2fs
UEFI FD    3 MiB（FD_BASE=0x9fc00000，FD_SIZE=0x300000）
```

## 已知边界

该端口作者自己只到 `Waiting on ... IOMedia ... Apple_HFS`（无 UFS 驱动）。即使内核完整编成，也只能到这一步；iOS 用户态需要 UFS 驱动，属于后续独立工程。
