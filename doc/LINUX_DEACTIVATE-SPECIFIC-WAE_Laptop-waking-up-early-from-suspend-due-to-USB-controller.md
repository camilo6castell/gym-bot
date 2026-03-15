# Fix: Laptop waking up early from suspend due to USB controller

## Context

A Linux laptop was configured to automatically suspend and wake up using the RTC (`wakealarm`) in order to execute a scheduled task related to reservation management.

The script scheduled a wake-up time correctly:

```
Next reservation: 2026-03-11 06:00:00-05:00
Scheduling wake at: 2026-03-11 05:58:00-05:00
```

The corresponding RTC timestamp stored in the system was:

```
/sys/class/rtc/rtc0/wakealarm
1773226680
```

Which converts to:

```
2026-03-11 05:58:00 -05 (America/Bogota)
```

This confirmed that the RTC scheduling mechanism was working correctly.

---

# Problem

Despite the RTC wake being scheduled for March 11, the system resumed only **~26 minutes after suspending**.

Logs showed:

```
Mar 09 07:50:17 kernel: PM: suspend entry (deep)
Mar 09 08:16:26 kernel: ACPI: PM: Low-level resume complete
```

Since the RTC wake was scheduled days later, this indicated that **another hardware device triggered the wake event**.

---

# Investigation

Wake sources were inspected using:

```
cat /proc/acpi/wakeup
```

Relevant output:

```
Device  S-state   Status   Sysfs node
XHC       S3    *enabled   pci:0000:00:14.0
```

The `XHC` device corresponds to the **Intel xHCI USB controller**:

```
00:14.0 USB controller: Intel Corporation 8 Series USB xHCI HC
Kernel driver: xhci_hcd
```

This controller manages all **USB 3 devices**, including:

* external hard drives
* USB hubs
* webcams
* Bluetooth adapters
* keyboards and mice

The only connected USB device was an **external USB hard drive**, which likely generated a hardware interrupt and woke the system.

---

# Solution

The wake capability of the USB controller was disabled.

Command used:

```
echo XHC | sudo tee /proc/acpi/wakeup
```

After running the command:

```
cat /proc/acpi/wakeup
```

Now shows:

```
XHC       S3    *disabled
```

This prevents the USB controller from waking the system from suspend.

---

# Making the Fix Persistent

Since `/proc/acpi/wakeup` resets on every boot, a **systemd service** was created to disable the wake source automatically.

## Create service

```
sudo nano /etc/systemd/system/disable-usb-wakeup.service
```

Service content:

```
[Unit]
Description=Disable USB wakeup
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo XHC > /proc/acpi/wakeup"

[Install]
WantedBy=multi-user.target
```

## Enable the service

```
sudo systemctl enable disable-usb-wakeup.service
```

Now the USB wake source is disabled automatically at every boot.

---

# Result

After applying this change:

* RTC wake scheduling remains functional.
* The system no longer wakes up due to USB device interrupts.
* Ethernet wake (`Wake-on-LAN`) remains available if needed.

The laptop now behaves as expected:

```
script → set RTC wake → suspend → wake only at scheduled time
```

---

# Notes

This type of issue is common on laptops because several hardware components can trigger wake events, including:

* USB controllers
* Ethernet (Wake-on-LAN)
* WiFi adapters
* lid sensors
* ACPI events

Inspecting and controlling wake sources through `/proc/acpi/wakeup` is a standard Linux troubleshooting method for power management issues.
