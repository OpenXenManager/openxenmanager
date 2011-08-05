messages = {}
messages_header = {}
messages_header['PBD_PLUG_FAILED_ON_SERVER_START'] = "Failed to attach storage on server boot"
messages['PBD_PLUG_FAILED_ON_SERVER_START'] = "\
A storage repository could not be attached when server '%s' started.\n \
You may be able to fix this using the 'Repair Storage'\n \
option in the Storage menu."
messages_header['HOST_SYNC_DATA_FAILED'] = "XenServer statistics synchronization failed"
messages['HOST_SYNC_DATA_FAILED'] = "\
%s. There was a temporary failure synchronizing performance statistics across the\n \
pool, probably because one or more servers were offline. Another\n \
synchronization attempt will be made later."

messages_header['host_alert_fs_usage'] = "File System On %s Full"
messages['host_alert_fs_usage'] = "\
Disk usage for the %s on server '%s' has reached %0.2f%%. XenServer's\n \
performance will be critically affected  if this disk becomes full.\n \
Log files or other non-essential (user created) files should be removed."
messages_header['alert_cpu_usage'] = "CPU Usage Alarm"
messages['alert_cpu_usage'] = "\
CPU usage on VM '%s' has been on average %0.2f%% for the last %d seconds.\n\
This alarm is set to be triggered when CPU usage is more than %0.1f%%"
messages_header['VM_SHUTDOWN'] = "VM shutdown"
messages['VM_SHUTDOWN'] = "\
VM '%s' has shut down."
messages_header['VM_STARTED'] = "VM started"
messages['VM_STARTED'] = "\
VM '%s' has started."
messages_header['VM_REBOOTED'] = "VM rebooted"
messages['VM_REBOOTED'] = "\
VM '%s' has rebooted."
messages_header['VM_SUSPENDED'] = "VM suspended"
messages['VM_SUSPENDED'] = "\
VM '%s' has suspended."
messages_header['VM_RESUMEND'] = "VM resumed"
messages['VM_RESUMED'] = "\
VM '%s' has resumed."

messages_header['restartHost'] = "After applying this update, all servers must be restarted."
messages_header['restartHVM'] = "After applying this update, all Linux VMs must be restarted."
messages_header['restartPV'] = "After applying this update, all Windows VMs must be restarted."
messages_header['restartXAPI'] = "After applying this update, all VMs must be restarted."

