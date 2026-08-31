# 接线说明

## reCamera 到 ESP32 的信号线

推荐接法：

```text
reCamera CAN0_RXD_M0 / GPIO5_D4 / GPIO188 -> ESP32 输入 GPIO
reCamera GND                              -> ESP32 GND
```

ESP32 示例：

```text
GPIO188 -> ESP32 GPIO20
GND     -> ESP32 GND
```

ESP32 的具体输入脚可以换，但要在 ESP32 程序里同步修改。

## 供电

不要用 reCamera 的 GPIO 给 ESP32 供电。

推荐供电拓扑：

```text
12 V/24 V 主电源
    +-> reCamera DC IN
    +-> DC-DC 降压模块 -> 5 V -> ESP32
```

必须共地：

```text
reCamera GND
ESP32 GND
DC-DC 降压模块 GND
```

## BAT 接口

`BAT` 通常表示电池接口，不是通用对外供电口。

不要默认认为它可以给 ESP32 供电。是否能对外放电、最大电流是多少、是否会影响充电管理，都必须看原理图和电源管理芯片设计。

## 上电前检查

1. 先不接 ESP32，只用万用表测试 GPIO188。
2. 确认 GPIO188 是 0 V / 3.3 V。
3. 确认 ESP32 单独供电正常。
4. 确认 reCamera GND 与 ESP32 GND 共地。
5. 再接 GPIO188 到 ESP32 输入脚。
