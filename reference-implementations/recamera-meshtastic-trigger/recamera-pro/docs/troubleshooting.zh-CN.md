# 故障排查

## GPIO 一直是 0 V

先看服务状态：

```bash
/etc/init.d/S99recamera_gpio_trigger status
```

看日志：

```bash
tail -n 100 /userdata/recamera_gpio_trigger.log
```

如果没有任何 `TRIGGER`，检查 AI 推理是否在运行：

```bash
curl -k -H "Authorization: Bearer $(python3 - <<'PY'
import json, ssl, urllib.request
ctx = ssl._create_unverified_context()
data = urllib.request.urlopen("https://127.0.0.1/cgi-bin/entry.cgi/web/setting", context=ctx).read()
print(json.loads(data.decode())["sApiKey"])
PY
)" "https://127.0.0.1/cgi-bin/entry.cgi/model/inference?id=0"
```

预期：

```json
{"iActualFPS":1,"iEnable":1,"sStatus":"running"}
```

如果 `iActualFPS` 是 0，重启推理：

```bash
curl -k -X POST -H "Authorization: Bearer $(python3 - <<'PY'
import json, ssl, urllib.request
ctx = ssl._create_unverified_context()
data = urllib.request.urlopen("https://127.0.0.1/cgi-bin/entry.cgi/web/setting", context=ctx).read()
print(json.loads(data.decode())["sApiKey"])
PY
)" "https://127.0.0.1/cgi-bin/entry.cgi/model/inference-restart?id=0"
```

## 视频窗口有框，但服务不触发

抓一条原始 WebSocket 消息：

```bash
python3 - <<'PY'
import asyncio, json, ssl, urllib.request, websockets

ctx = ssl._create_unverified_context()
data = urllib.request.urlopen("https://127.0.0.1/cgi-bin/entry.cgi/web/setting", context=ctx).read()
token = json.loads(data.decode())["sApiKey"]

async def main():
    async with websockets.connect(
        "wss://127.0.0.1/ws/inference/results",
        extra_headers={"Authorization": "Bearer " + token},
        ssl=ctx,
    ) as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=20)
        print(raw)

asyncio.run(main())
PY
```

确认里面是否有：

```text
"class_name":"person"
```

如果类别不同，修改：

```text
/userdata/recamera_trigger.conf
```

例如：

```ini
TARGET_CLASS=cat
```

然后重启：

```bash
/etc/init.d/S99recamera_gpio_trigger restart
```

## 想临时降低阈值

编辑：

```bash
vi /userdata/recamera_trigger.conf
```

把：

```ini
MIN_SCORE=0.5
```

改成：

```ini
MIN_SCORE=0.1
```

重启：

```bash
/etc/init.d/S99recamera_gpio_trigger restart
```

测试完成后建议改回 `0.5`。

## GPIO 测试可以翻转，但正式服务不触发

说明硬件 GPIO 是好的，重点排查：

```text
AI 推理是否输出 detection.entries
TARGET_CLASS 是否匹配
MIN_SCORE 是否太高
服务日志里是否有 connection/error
```

## GPIO 测试也不能翻转

检查是否用 root 执行：

```bash
id
```

预期：

```text
uid=0(root)
```

普通用户通常不能写：

```text
/sys/class/gpio/export
```
