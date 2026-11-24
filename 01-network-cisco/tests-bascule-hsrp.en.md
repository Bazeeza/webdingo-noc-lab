# HSRP failover tests

[![Français](https://img.shields.io/badge/Langue-Français-3fe0a0?style=for-the-badge)](tests-bascule-hsrp.md)
[![English](https://img.shields.io/badge/Language-English-2b9dff?style=for-the-badge)](tests-bascule-hsrp.en.md)

Redundancy that has never been tested is not redundancy. This page describes how to prove
that the network survives the loss of the primary Internet link, then the complete loss of the
primary router, and what must be observed at each step.

## Preparation

- A workstation in VLAN 2 (USERS) and a server in VLAN 1.
- A console session on each router.
- A continuous ping from the workstation to the Internet, to measure the outage:
  ```
  ping -t 8.8.8.8
  ```
- Zabbix open on *Monitoring > Problems*.

## Test 1: normal state

On Routeur1:

```
Routeur1# show standby brief
                     P indicates configured to preempt.
                     |
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Gi0/0.1     1    110 P Active  local           192.168.5.2     192.168.5.254
Gi0/0.2     2    110 P Active  local           192.168.6.2     192.168.6.254
```

**Expected**: Routeur1 is *Active* (priority 110) on both groups, Routeur2 is *Standby*.
On the workstation, `tracert 8.8.8.8` goes through the gateway `192.168.6.254`.

## Test 2: loss of the primary Internet link

Simulate a failure of the primary provider on Routeur1:

```
Routeur1(config)# interface GigabitEthernet0/1
Routeur1(config-if)# shutdown
```

**Expected**:

- `show track 1`: the state changes to *Down*;
- the priority of Routeur1 drops to 90 (110 - 20), below that of Routeur2 (100);
- Routeur2 becomes *Active* (preemption); `show standby brief` on Routeur2 confirms it;
- the continuous ping loses a few packets at most, then resumes through the backup link;
- Zabbix raises the status alert for interface Gi0/1 of Routeur1.

> Connections already open (download, SSH session) are cut: the NAT of Routeur2
> uses another public address. New connections work right away.

## Test 3: primary link back

```
Routeur1(config-if)# no shutdown
```

**Expected**: the tracking object goes back to *Up*, Routeur1 gets priority 110 back and takes
the *Active* role again on its own thanks to `preempt`. The Zabbix alert closes automatically.

## Test 4: complete failure of the primary router

Unplug the power of Routeur1.

**Expected**:

- Routeur2 no longer receives the *hello* messages of Routeur1 and becomes *Active* after the
  *hold* time (10 seconds by default);
- the continuous ping loses a few seconds of packets, then resumes;
- Zabbix reports Routeur1 as unreachable (SNMP and ping).

When Routeur1 is powered back on: it takes the *Active* role back (preemption), and the
"router recently restarted" alert (uptime below 1 hour) appears in Zabbix.

## Results grid

| Test | Expected | Packets lost | Result |
|---|---|---|---|
| 1. Normal state | Routeur1 *Active* | 0 | ☐ |
| 2. Primary link cut | Routeur2 *Active*, Internet maintained | a few | ☐ |
| 3. Link restored | Routeur1 takes *Active* back | 0 to 1 | ☐ |
| 4. Routeur1 powered off | Routeur2 *Active* after ~10 s | a few seconds | ☐ |

## Reducing the failover time

The default HSRP timers (hello 3 s, hold 10 s) can be reduced on both routers:

```
standby 1 timers msec 250 msec 750
standby 2 timers msec 250 msec 750
```

Failover after a complete failure then drops below one second, at the cost of a little more
control traffic.
