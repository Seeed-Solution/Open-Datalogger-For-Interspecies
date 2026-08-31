# 原理说明

reCamera Pro 会在设备内部运行 AI 模型，例如 `yolox_s.rknn`。模型每一帧推理后，会产生检测结果。

本程序不读取串口输出，而是订阅 reCamera 本机的 WebSocket 推理结果：

```text
wss://127.0.0.1/ws/inference/results
```

实际验证到的消息结构类似：

```json
{
  "task_type": 1,
  "task_type_name": "detection",
  "model_id": 0,
  "detection": {
    "entries": [
      {
        "box": {
          "left": 0.389,
          "top": 0.334,
          "right": 0.491,
          "bottom": 0.519
        },
        "score": 0.88,
        "class_id": 0,
        "class_name": "person"
      }
    ],
    "count": 1
  }
}
```

程序逻辑：

```text
1. 连接 /ws/inference/results
2. 读取 detection.entries
3. 查找 class_name 等于配置里的 TARGET_CLASS
4. 判断 score 是否大于等于 MIN_SCORE
5. 如果满足条件，拉高配置里的 GPIO
6. 等待 PULSE_SECONDS
7. 拉低 GPIO
8. 进入 COOLDOWN_SECONDS 冷却期
```

默认配置：

```text
TARGET_CLASS=person
MIN_SCORE=0.5
GPIO=188
PULSE_SECONDS=3
COOLDOWN_SECONDS=60
```

## 为什么需要 root

本程序使用 Linux GPIO sysfs 接口：

```text
/sys/class/gpio/export
/sys/class/gpio/gpio188/direction
/sys/class/gpio/gpio188/value
```

这些文件通常需要 root 权限写入。所以安装脚本会把服务放到 `/etc/init.d/`，让设备开机时以 root 身份启动。

## 与 12 V 工业 IO 的区别

reCamera 的 GPIO Manager API 只能控制厂商暴露的工业 IO，例如之前验证过的 12 V 输出。

本程序不使用那两个 12 V 输出，而是直接控制 SoC 的 3.3 V 逻辑 GPIO。

适用场景：

```text
GPIO188 -> ESP32 输入脚
GND     -> ESP32 GND
```

不适合：

```text
直接驱动电机、继电器线圈、大电流负载
给 ESP32 供电
```
