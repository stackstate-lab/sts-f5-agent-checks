# F5


## Installation Steps

Follow [video instructions](https://www.youtube.com/watch?v=xCAUKBhcR9c&t=2s)

### Create VM

- Create an F5 account.
- List [virtual editions](https://downloads.f5.com/esd/eula.sv?sw=BIG-IP&pro=big-ip_v16.x&ver=16.1.3&container=Virtual-Edition&path=&file=&B1=I+Accept)
- Select VMWare image to download: BIGIP-16.1.3-0.0.12.ALL-vmware.ova
- In VMWare Fusion select import from file menu and select downloaded file
- Accept license, then select 2 cpu / 4096 ram, change vm name and click continue.
- After import select "customize"
- Disable  network adapters 2, 3 and 4
- On main network adapter select vmnet10 (172.16.253.0 / 255.255.255.0)
- Save and start.

### Configure IP

- Login to shell: root / default
- Change password to root / @dmin1234
- Run config command
- Select ipv4 and select no when asked to use automatic configuration
- Type address 172.16.253.20, keep default netmask, change route to 172.16.253.1
- Confirm changes.

### License

- [Go to User Interface](https://172.16.253.200/tmui/login.jsp)
- login admin / @dmin1234
- Change password to 2zrRdQ8PYpK5Bsz
- Go to f5.com and ask for a trial license. You have to login and register for Bip IP
- They will send you an email.  Copy the base key.
- Paste it in the web ui. Turn to manual activation and click next.
- Follow inststructions on screen.

### Freezing time
- Change the vm vmx file to start with day of installation as start date, so never expires.
- See http://sanbarrow.com/vmx/vmx-always-start-tonight.html
- On F5 vm : https://www.cyberciti.biz/faq/howto-set-date-time-from-linux-command-prompt/
  - hwclock -r
  - date -s "2 JUL 2022 13:00:00"
  - hwclock -w

### Setup VLANS

- Configure network adapter 2 to vmnet12 : 192.168.10.0/24
- Configure network adapter 1 to vmnet11 : 10.10.10.0/24
- VLAN [page](https://172.16.253.200/xui/?nocache=1657192898379#)
- Setup external and internal vlan
- Setup self ips
  - ExternalVlan : 192.168.10.2
  - InternalVlan : 10.10.10.2

