# 触发抓拍与照片下载

GPIO188 触发程序可以在真正触发电平时保存一张现场照片，用来判断触发是否真实有效。

## 默认策略

```text
触发类别：person 或 cat
GPIO 输出：GPIO188 拉高 3 秒
抓拍时机：GPIO188 触发同一时刻
照片目录：/mnt/rc_mmcblk0p8/recamera_trigger_snapshots
照片上限：1000 张
清理规则：达到 1000 张后，删除最旧的 100 张
压缩方式：ffmpeg 逐级压缩，目标约 500 KB
最小保留空间：/mnt 所在分区剩余空间低于 1024 MB 时跳过抓拍
```

文件名示例：

```text
20260831_114500_person_0.92_gpio188.jpg
20260831_114530_cat_0.71_gpio188.jpg
```

每次抓拍还会写入事件 CSV：

```text
/mnt/rc_mmcblk0p8/recamera_trigger_snapshots/trigger_events.csv
```

里面包含：

```text
timestamp_iso
class_name
score
gpio
snapshot_path
snapshot_status
snapshot_size_bytes
note
```

## 为什么目录在 /mnt 下

reCamera 官方 HTTP 捕获接口要求输出路径以 `/mnt` 开头，所以照片目录使用：

```text
/mnt/rc_mmcblk0p8/recamera_trigger_snapshots
```

这个路径仍然是设备本机存储，可以通过 SSH/SCP 远程读取。

## 远程下载照片

下载最近 100 张：

```bash
python3 "OpenDataLogger/ReCamera pro/scripts/download_snapshots.py" \
  --host 192.168.50.94 \
  --user root \
  --latest 100 \
  --output-dir ./recamera_trigger_snapshots
```

如果使用 `sshpass` 自动输入密码：

```bash
SSHPASS='你的密码' python3 "OpenDataLogger/ReCamera pro/scripts/download_snapshots.py" \
  --host 192.168.50.94 \
  --user root \
  --latest 100 \
  --use-sshpass-env
```

也可以直接用 `scp` 拉整个目录：

```bash
scp -r root@192.168.50.94:/mnt/rc_mmcblk0p8/recamera_trigger_snapshots ./recamera_trigger_snapshots
```

## 修改抓拍配置

设备配置文件：

```text
/userdata/recamera_trigger.conf
```

相关参数：

```ini
SAVE_SNAPSHOT=1
SNAPSHOT_DIR=/mnt/rc_mmcblk0p8/recamera_trigger_snapshots
SNAPSHOT_EVENT_CSV=/mnt/rc_mmcblk0p8/recamera_trigger_snapshots/trigger_events.csv
SNAPSHOT_MAX_FILES=1000
SNAPSHOT_DELETE_BATCH=100
SNAPSHOT_MIN_FREE_MB=1024
SNAPSHOT_COMPRESS=1
SNAPSHOT_FFMPEG_Q=5
SNAPSHOT_TARGET_KB=500
```

修改后重启：

```bash
/etc/init.d/S99recamera_gpio_trigger restart
```

当前测试设备使用的现场服务名可能是：

```bash
/etc/init.d/S99person_gpio188 restart
```
