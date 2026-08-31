# GPIO 引脚表

Linux GPIO 编号计算公式：

```text
GPIO bank * 32 + 字母组 * 8 + 编号
```

字母组：

```text
A = 0
B = 1
C = 2
D = 3
```

## 已验证默认脚

```text
CAN0_RXD_M0 / GPIO5_D4
= 5 * 32 + 3 * 8 + 4
= 188
```

这个脚已经验证可以作为 3.3 V 逻辑 GPIO 输出。

## CAN 口复用 GPIO

| 物理功能标注 | 复用 GPIO | Linux GPIO | 计算 |
|---|---:|---:|---|
| CAN0_RXD_M0 | GPIO5_D4 | 188 | 5*32 + 3*8 + 4 |
| CAN0_TXD_M0 | GPIO5_D5 | 189 | 5*32 + 3*8 + 5 |
| CAN1_RXD_M0 | GPIO5_D6 | 190 | 5*32 + 3*8 + 6 |
| CAN1_TXD_M0 | GPIO5_D7 | 191 | 5*32 + 3*8 + 7 |

注意：这些脚如果被配置成 GPIO，就不要同时用于 CAN 通信。

## UART 口复用 GPIO

| 物理功能标注 | 复用 GPIO | Linux GPIO | 计算 |
|---|---:|---:|---|
| UART4_TX_M1 | GPIO5_A2 | 162 | 5*32 + 0*8 + 2 |
| UART4_RX_M1 | GPIO5_A3 | 163 | 5*32 + 0*8 + 3 |

本项目最终没有使用 A2/A3。实测 GPIO188 更适合当前这台设备。

## 验证命令

测试任意 GPIO：

```bash
sh test_gpio_toggle.sh 188
```

把 `188` 换成目标编号即可。

万用表测量：

```text
红表笔：目标 GPIO
黑表笔：GND
```

预期：

```text
每 5 秒在 0 V 和约 3.3 V 之间切换
```
