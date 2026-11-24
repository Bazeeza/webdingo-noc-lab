# Incident runbooks

[![Français](https://img.shields.io/badge/Langue-Français-3fe0a0?style=for-the-badge)](README.md)
[![English](https://img.shields.io/badge/Language-English-2b9dff?style=for-the-badge)](README.en.md)

What to do when an alert fires. Every sheet follows the same order: **what it means,
the impact, check, act, escalate**. The GLPI ticket is created automatically for *High*
alerts; the technician records each step in it, then closes it with the cause found.

| Zabbix alert | Severity | Sheet |
|---|---|---|
| Interface Gi0/1 status: DOWN | High | [1. Primary Internet link down](#1-primary-internet-link-down) |
| Inbound bandwidth > 60 % / > 85 % | Warning / High | [2. Link saturation](#2-link-saturation) |
| Errors or discarded packets on Gi0/1 | Warning / High | [3. Interface errors](#3-interface-errors) |
| ICMP packet loss, latency | Warning / High | [4. Degraded link](#4-degraded-link) |
| Uptime < 1 h / < 5 min | Warning / High | [5. Router restart](#5-router-restart) |
| Established TCP connections > 100 / > 200 | Warning / High | [6. Abnormal TCP connections](#6-abnormal-tcp-connections) |
| High router CPU or memory | Warning / High | [7. Overloaded router](#7-overloaded-router) |
| Disk space < 20 % / < 10 % | Warning / High | [8. Server disk almost full](#8-server-disk-almost-full) |

---

## 1. Primary Internet link down

**What it means**: the WAN interface of Routeur1 is out of service.
**Expected impact**: none for users if HSRP has failed over; connections opened
before the failure are cut.

**Check**

```
Routeur1# show ip interface brief
Routeur1# show interfaces GigabitEthernet0/1
Routeur1# show track 1
Routeur2# show standby brief
```

- Routeur2 must be *Active* on both groups. Otherwise, go straight to escalation.
- `administratively down`: someone ran `shutdown`; `down/down`: cable, port or provider.

**Act**

1. Check the cable and the LEDs of port Gi0/1, then the provider's equipment.
2. If the interface is up but has no address: `show dhcp lease`, then `shutdown` / `no shutdown`.
3. When the link returns, confirm that Routeur1 takes the *Active* role back (preemption).

**Escalate**: to the Internet provider if the link stays down for more than 15 minutes; urgently
if Routeur2 has not taken over (Internet down for everyone).

## 2. Link saturation

**What it means**: inbound traffic on Gi0/1 exceeds 60 % (Warning) or 85 % (High)
of the capacity for 5 minutes.
**Expected impact**: slow browsing, choppy VoIP calls, web applications that time out.

**Check**

```
Routeur1# show interfaces GigabitEthernet0/1 | include rate
Routeur1# show ip nat translations
Routeur1# show ip nat statistics
```

- In Grafana, check whether the rise is sudden (one-off transfer) or gradual (real need).
- In the NAT translations, find the internal address with the most sessions.

**Act**

1. Identify the workstation or server involved and what it is doing (update, backup, download).
2. Legitimate traffic at the wrong time (backup during the day): reschedule it outside business hours.
3. Abnormal traffic: isolate the workstation (switch port in `shutdown`) and handle it as a security incident.

**Escalate**: if the saturation comes back every day, propose more capacity
or quality of service (QoS); if the traffic is suspicious, to the security team.

## 3. Interface errors

**What it means**: packets arrive or leave corrupted, or are discarded.
A healthy interface stays at 0.
**Expected impact**: retransmissions, slowness, packet loss.

**Check**

```
Routeur1# show interfaces GigabitEthernet0/1 | include errors|CRC|drops|duplex
```

- CRC errors or *input errors*: almost always physical (cable, connector, port).
- Discards without errors: congestion (see sheet 2).
- Bad negotiation: check that speed and duplex are the same on both sides.

**Act**

1. Reset the counters to measure cleanly: `clear counters GigabitEthernet0/1`.
2. Replace the cable, then the port if the errors come back.
3. Fix the duplex if both sides do not match.

**Escalate**: to the provider if the errors persist with a new cable and port.

## 4. Degraded link

**What it means**: the link answers but loses packets (> 10 % or > 50 %) or the latency
exceeds 100 ms.
**Expected impact**: robotic VoIP, unstable VPNs, pages that reload.

**Check**

```
Routeur1# ping 8.8.8.8 repeat 100
Routeur1# traceroute 8.8.8.8
```

- Does the loss start at the first hop (internal network), at the router, or at the provider?
- Compare with Routeur2: if its link is healthy, fail over to it on purpose.

**Act**

1. Internal problem: see sheets 3 and 7.
2. Provider problem: move the traffic to the backup link by lowering the
   HSRP priority of Routeur1 (`standby 1 priority 90`, `standby 2 priority 90`), then set it
   back to 110 once the problem is fixed.

**Escalate**: to the provider, with the ping and traceroute results.

## 5. Router restart

**What it means**: the uptime is below 1 hour (Warning) or 5 minutes (High).
**Expected impact**: a short outage during the restart if it was the active router.

**Check**

```
Routeur1# show version | include uptime|returned
Routeur1# show logging
```

- *returned to ROM by reload*: manual restart. Was it planned?
- *power-on*: power failure. Check the UPS and the power supply.
- *crash* or error message: save the log and the crash file.

**Act**

1. Confirm that the configuration is complete: `show running-config` compared with the reference configuration.
2. Check that HSRP is back to its normal state (`show standby brief`).

**Escalate**: to the manufacturer if the router restarts several times or after a crash.

## 6. Abnormal TCP connections

**What it means**: the router has more than 100 (Warning) or 200 (High) established TCP
connections. These are connections **to the router itself**: management sessions or an attack.
**Expected impact**: high CPU, slow router management, risk of denial of service.

**Check**

```
Routeur1# show tcp brief all
Routeur1# show users
Routeur1# show processes cpu sorted
```

- Find the source addresses: known internal workstations, or unknown addresses?

**Act**

1. Forgotten management sessions: `clear line` to close them.
2. Unknown sources: block them with an access list and limit management to the
   administration addresses (`access-class` on the VTY lines).
3. Keep the evidence (command outputs, time) in the ticket.

**Escalate**: to the security team as soon as an unknown source is involved.

## 7. Overloaded router

**What it means**: CPU above 60 % / 90 %, or memory above 70 % / 90 %.
**Expected impact**: latency, slower routing and NAT, risk of a crash.

**Check**

```
Routeur1# show processes cpu sorted
Routeur1# show processes cpu history
Routeur1# show memory statistics
```

**Act**

1. Identify the process involved (NAT, SNMP polled too often, attack: see sheet 6).
2. If it is the normal load: plan a more powerful device.

**Escalate**: to the manufacturer if a process leaks memory.

## 8. Server disk almost full

**What it means**: less than 20 % (Warning) or 10 % (High) free on `/`.
**Expected impact**: Zabbix or GLPI database stopped, logs lost.

**Check**

```
df -h /
sudo du -xh / --max-depth=2 2>/dev/null | sort -h | tail -15
sudo journalctl --disk-usage
```

**Act**

1. Reduce the system logs: `sudo journalctl --vacuum-time=14d`.
2. Remove the cached packages: `sudo apt-get clean`.
3. On Zabbix: check the retention period of the history (31 days) and of the trends (365 days).
4. If space is still missing: extend the virtual disk.

**Escalate**: to the system team if the growth continues despite the cleanup.

---

## Closing an incident

1. Confirm that the Zabbix alert is back to the *Resolved* state.
2. In the GLPI ticket: cause, actions taken, duration of the impact.
3. If the cause can come back: create a prevention task (cable replacement, QoS, capacity).
