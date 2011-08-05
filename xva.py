#!/usr/bin/env python

## Author: David Markey <david.markey@citrix.com>, Citrix Systems.

## Licence: GNU LESSER GENERAL PUBLIC LICENSE V3, http://www.gnu.org/licenses/lgpl-3.0.txt

## THIS SOFTWARE COMES WITH ABSOLUTELY NO WARRANTY! USE AT YOUR OWN RISK!

## README before use.



__version__ = "1.1.0"



import os
import tarfile
import cStringIO
import sys
import copy

## Legacy Python 2.4 stuff

try:
    import xml.etree.ElementTree as ET
except:
    import elementtree.ElementTree as ET

try:
    from hashlib import sha1
except:
    from sha import sha as sha1

try:
    from uuid import uuid1 as uuid
except:
    ## RHEL/Python 2.4 is missing uuid, Dirty hack here
    import commands
    def uuid():
        return commands.getoutput("uuidgen")
        

os.SEEK_SET, os.SEEK_CUR, os.SEEK_END = range(3)

## XML BLOB !##


XML_DATA="<value>  <struct>    <member>      <name>version</name>      <value>        <struct>          <member>            <name>hostname</name>            <value>cheesy-2</value>          </member>          <member>            <name>date</name>            <value>2009-12-02</value>          </member>          <member>            <name>product_version</name>            <value>5.5.0</value>          </member>          <member>            <name>product_brand</name>            <value>XenServer</value>          </member>          <member>            <name>build_number</name>            <value>24648p</value>          </member>          <member>            <name>xapi_major</name>            <value>1</value>          </member>          <member>            <name>xapi_minor</name>            <value>3</value>          </member>          <member>            <name>export_vsn</name>            <value>2</value>          </member>        </struct>      </value>    </member>    <member>      <name>objects</name>      <value>        <array>          <data>            <value>              <struct>                <member>                  <name>class</name>                  <value>VM</value>                </member>                <member>                  <name>id</name>                  <value>Ref:0</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID1</value>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>export</value>                              <value>clone</value>                              <value>copy</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct>                            <member>                              <name>OpaqueRef:NULL</name>                              <value>export</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>power_state</name>                        <value>Halted</value>                      </member>                      <member>                        <name>name_label</name>                        <value>~Unnamed</value>                      </member>                      <member>                        <name>name_description</name>                        <value/>                      </member>                      <member>                        <name>user_version</name>                        <value>1</value>                      </member>                      <member>                        <name>is_a_template</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>suspend_VDI</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>resident_on</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>affinity</name>                        <value>OpaqueRef:b8c1cff1-2b1a-04c6-cf05-e8f832a0c369</value>                      </member>                      <member>                        <name>memory_target</name>                        <value>268435456</value>                      </member>                      <member>                        <name>memory_static_max</name>                        <value>268435456</value>                      </member>                      <member>                        <name>memory_dynamic_max</name>                        <value>268435456</value>                      </member>                      <member>                        <name>memory_dynamic_min</name>                        <value>268435456</value>                      </member>                      <member>                        <name>memory_static_min</name>                        <value>16777216</value>                      </member>                      <member>                        <name>VCPUs_params</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VCPUs_max</name>                        <value>1</value>                      </member>                      <member>                        <name>VCPUs_at_startup</name>                        <value>1</value>                      </member>                      <member>                        <name>actions_after_shutdown</name>                        <value>destroy</value>                      </member>                      <member>                        <name>actions_after_reboot</name>                        <value>restart</value>                      </member>                      <member>                        <name>actions_after_crash</name>                        <value>restart</value>                      </member>                      <member>                        <name>consoles</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>VIFs</name>                        <value>                          <array>                            <data>                              <value>Ref:1</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>VBDs</name>                        <value>                          <array>                            <data>                              <value>Ref:3</value>                              <value>Ref:6</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>crash_dumps</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>VTPMs</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>PV_bootloader</name>                        <value/>                      </member>                      <member>                        <name>PV_kernel</name>                        <value/>                      </member>                      <member>                        <name>PV_ramdisk</name>                        <value/>                      </member>                      <member>                        <name>PV_args</name>                        <value/>                      </member>                      <member>                        <name>PV_bootloader_args</name>                        <value/>                      </member>                      <member>                        <name>PV_legacy_args</name>                        <value/>                      </member>                      <member>                        <name>HVM_boot_policy</name>                        <value>BIOS order</value>                      </member>                      <member>                        <name>HVM_boot_params</name>                        <value>                          <struct>                            <member>                              <name>order</name>                              <value>dc</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>HVM_shadow_multiplier</name>                        <value>                          <double>1</double>                        </value>                      </member>                      <member>                        <name>platform</name>                        <value>                          <struct>                            <member>                              <name>nx</name>                              <value>false</value>                            </member>                            <member>                              <name>acpi</name>                              <value>true</value>                            </member>                            <member>                              <name>apic</name>                              <value>true</value>                            </member>                            <member>                              <name>pae</name>                              <value>true</value>                            </member>                            <member>                              <name>viridian</name>                              <value>true</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>PCI_bus</name>                        <value/>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct>                            <member>                              <name>install-methods</name>                              <value>cdrom</value>                            </member>                            <member>                              <name>mac_seed</name>                              <value></value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>domid</name>                        <value>-1</value>                      </member>                      <member>                        <name>domarch</name>                        <value/>                      </member>                      <member>                        <name>last_boot_CPU_flags</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>is_control_domain</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>metrics</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>guest_metrics</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>last_booted_record</name>                        <value/>                      </member>                      <member>                        <name>recommendations</name>                        <value>&lt;restrictions&gt;&lt;restriction field=&quot;memory-static-max&quot; max=&quot;34359738368&quot; /&gt;&lt;restriction field=&quot;vcpus-max&quot; max=&quot;8&quot; /&gt;&lt;restriction property=&quot;number-of-vbds&quot; max=&quot;7&quot; /&gt;&lt;restriction property=&quot;number-of-vifs&quot; max=&quot;7&quot; /&gt;&lt;/restrictions&gt;</value>                      </member>                      <member>                        <name>xenstore_data</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>ha_always_run</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>ha_restart_priority</name>                        <value/>                      </member>                      <member>                        <name>is_a_snapshot</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>snapshot_of</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>snapshots</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>snapshot_time</name>                        <value>                          <dateTime.iso8601>19700101T00:00:00Z</dateTime.iso8601>                        </value>                      </member>                      <member>                        <name>transportable_snapshot_id</name>                        <value/>                      </member>                      <member>                        <name>blobs</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>blocked_operations</name>                        <value>                          <struct/>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>VBD</value>                </member>                <member>                  <name>id</name>                  <value>Ref:6</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID2</value>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>attach</value>                              <value>eject</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VM</name>                        <value>Ref:0</value>                      </member>                      <member>                        <name>VDI</name>                        <value>Ref:7</value>                      </member>                      <member>                        <name>device</name>                        <value/>                      </member>                      <member>                        <name>userdevice</name>                        <value>3</value>                      </member>                      <member>                        <name>bootable</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>mode</name>                        <value>RO</value>                      </member>                      <member>                        <name>type</name>                        <value>CD</value>                      </member>                      <member>                        <name>unpluggable</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>storage_lock</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>empty</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>currently_attached</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>status_code</name>                        <value>0</value>                      </member>                      <member>                        <name>status_detail</name>                        <value/>                      </member>                      <member>                        <name>runtime_properties</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_algorithm_type</name>                        <value/>                      </member>                      <member>                        <name>qos_algorithm_params</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_supported_algorithms</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>metrics</name>                        <value>OpaqueRef:NULL</value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>VBD</value>                </member>                <member>                  <name>id</name>                  <value>Ref:3</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID3</value>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>attach</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VM</name>                        <value>Ref:0</value>                      </member>                      <member>                        <name>VDI</name>                        <value>Ref:4</value>                      </member>                      <member>                        <name>device</name>                        <value>xvda</value>                      </member>                      <member>                        <name>userdevice</name>                        <value>0</value>                      </member>                      <member>                        <name>bootable</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>mode</name>                        <value>RW</value>                      </member>                      <member>                        <name>type</name>                        <value>Disk</value>                      </member>                      <member>                        <name>unpluggable</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>storage_lock</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>empty</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct>                            <member>                              <name>owner</name>                              <value>true</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>currently_attached</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>status_code</name>                        <value>0</value>                      </member>                      <member>                        <name>status_detail</name>                        <value/>                      </member>                      <member>                        <name>runtime_properties</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_algorithm_type</name>                        <value/>                      </member>                      <member>                        <name>qos_algorithm_params</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_supported_algorithms</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>metrics</name>                        <value>OpaqueRef:NULL</value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>VIF</value>                </member>                <member>                  <name>id</name>                  <value>Ref:1</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID4</value>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>attach</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>device</name>                        <value>0</value>                      </member>                      <member>                        <name>network</name>                        <value>Ref:2</value>                      </member>                      <member>                        <name>VM</name>                        <value>Ref:0</value>                      </member>                      <member>                        <name>MAC</name>                        <value>00:00:00:00:00:00</value>                      </member>                      <member>                        <name>MTU</name>                        <value>0</value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>currently_attached</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>status_code</name>                        <value>0</value>                      </member>                      <member>                        <name>status_detail</name>                        <value/>                      </member>                      <member>                        <name>runtime_properties</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_algorithm_type</name>                        <value/>                      </member>                      <member>                        <name>qos_algorithm_params</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>qos_supported_algorithms</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>metrics</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>MAC_autogenerated</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>network</value>                </member>                <member>                  <name>id</name>                  <value>Ref:2</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID5</value>                      </member>                      <member>                        <name>name_label</name>                        <value>Pool-wide network associated with eth0</value>                      </member>                      <member>                        <name>name_description</name>                        <value/>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VIFs</name>                        <value>                          <array>                            <data>                              <value>Ref:1</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>PIFs</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>bridge</name>                        <value>xenbr0</value>                      </member>                      <member>                        <name>blobs</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>VDI</value>                </member>                <member>                  <name>id</name>                  <value>Ref:7</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID6</value>                      </member>                      <member>                        <name>name_label</name>                        <value>IDE 0.0</value>                      </member>                      <member>                        <name>name_description</name>                        <value/>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>SR</name>                        <value>Ref:8</value>                      </member>                      <member>                        <name>VBDs</name>                        <value>                          <array>                            <data>                              <value>Ref:6</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>crash_dumps</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>virtual_size</name>                        <value>4294965248</value>                      </member>                      <member>                        <name>physical_utilisation</name>                        <value>4294965248</value>                      </member>                      <member>                        <name>type</name>                        <value>user</value>                      </member>                      <member>                        <name>sharable</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>read_only</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>storage_lock</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>location</name>                        <value>/dev/xapi/cd/hda</value>                      </member>                      <member>                        <name>managed</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>missing</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>parent</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>xenstore_data</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>sm_config</name>                        <value>                          <struct>                            <member>                              <name>hotplugged_at</name>                              <value>2010-02-10T10:39:52Z</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>is_a_snapshot</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>snapshot_of</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>snapshots</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>snapshot_time</name>                        <value>                          <dateTime.iso8601>19700101T00:00:00Z</dateTime.iso8601>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>VDI</value>                </member>                <member>                  <name>id</name>                  <value>Ref:4</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID7</value>                      </member>                      <member>                        <name>name_label</name>                        <value>0</value>                      </member>                      <member>                        <name>name_description</name>                        <value/>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>clone</value>                              <value>destroy</value>                              <value>resize</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>SR</name>                        <value>Ref:5</value>                      </member>                      <member>                        <name>VBDs</name>                        <value>                          <array>                            <data>                              <value>Ref:3</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>crash_dumps</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>virtual_size</name>                        <value>5368709120</value>                      </member>                      <member>                        <name>physical_utilisation</name>                        <value>5385486336</value>                      </member>                      <member>                        <name>type</name>                        <value>system</value>                      </member>                      <member>                        <name>sharable</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>read_only</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>storage_lock</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>location</name>                        <value>ebe16ffc-7f5d-4761-9cfe-2f052577d64d</value>                      </member>                      <member>                        <name>managed</name>                        <value>                          <boolean>1</boolean>                        </value>                      </member>                      <member>                        <name>missing</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>parent</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>xenstore_data</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>sm_config</name>                        <value>                          <struct>                            <member>                              <name>vdi_type</name>                              <value>vhd</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>is_a_snapshot</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>snapshot_of</name>                        <value>OpaqueRef:NULL</value>                      </member>                      <member>                        <name>snapshots</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>snapshot_time</name>                        <value>                          <dateTime.iso8601>19700101T00:00:00Z</dateTime.iso8601>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>SR</value>                </member>                <member>                  <name>id</name>                  <value>Ref:5</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID8</value>                      </member>                      <member>                        <name>name_label</name>                        <value>Local storage</value>                      </member>                      <member>                        <name>name_description</name>                        <value/>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>forget</value>                              <value>vdi_create</value>                              <value>vdi_snapshot</value>                              <value>plug</value>                              <value>update</value>                              <value>destroy</value>                              <value>vdi_destroy</value>                              <value>scan</value>                              <value>vdi_clone</value>                              <value>vdi_resize</value>                              <value>unplug</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VDIs</name>                        <value>                          <array>                            <data>                              <value>Ref:4</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>PBDs</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>virtual_allocation</name>                        <value>39313211392</value>                      </member>                      <member>                        <name>physical_utilisation</name>                        <value>39325794304</value>                      </member>                      <member>                        <name>physical_size</name>                        <value>71777124352</value>                      </member>                      <member>                        <name>type</name>                        <value>lvm</value>                      </member>                      <member>                        <name>content_type</name>                        <value>user</value>                      </member>                      <member>                        <name>shared</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct>                            <member>                              <name>i18n-original-value-name_label</name>                              <value>Local storage</value>                            </member>                            <member>                              <name>i18n-key</name>                              <value>local-storage</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>sm_config</name>                        <value>                          <struct>                            <member>                              <name>allocation</name>                              <value>thick</value>                            </member>                            <member>                              <name>use_vhd</name>                              <value>true</value>                            </member>                            <member>                              <name>devserial</name>                              <value>scsi-SATA_WDC_WD800JD-75M_WD-WMAM9AAE1521</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>blobs</name>                        <value>                          <struct/>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>            <value>              <struct>                <member>                  <name>class</name>                  <value>SR</value>                </member>                <member>                  <name>id</name>                  <value>Ref:8</value>                </member>                <member>                  <name>snapshot</name>                  <value>                    <struct>                      <member>                        <name>uuid</name>                        <value>UUID9</value>                      </member>                      <member>                        <name>name_label</name>                        <value>DVD drives</value>                      </member>                      <member>                        <name>name_description</name>                        <value>Physical DVD drives</value>                      </member>                      <member>                        <name>allowed_operations</name>                        <value>                          <array>                            <data>                              <value>forget</value>                              <value>vdi_introduce</value>                              <value>plug</value>                              <value>update</value>                              <value>destroy</value>                              <value>scan</value>                              <value>vdi_clone</value>                              <value>unplug</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>current_operations</name>                        <value>                          <struct/>                        </value>                      </member>                      <member>                        <name>VDIs</name>                        <value>                          <array>                            <data>                              <value>Ref:7</value>                            </data>                          </array>                        </value>                      </member>                      <member>                        <name>PBDs</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>virtual_allocation</name>                        <value>4294965248</value>                      </member>                      <member>                        <name>physical_utilisation</name>                        <value>4294965248</value>                      </member>                      <member>                        <name>physical_size</name>                        <value>4294965248</value>                      </member>                      <member>                        <name>type</name>                        <value>udev</value>                      </member>                      <member>                        <name>content_type</name>                        <value>iso</value>                      </member>                      <member>                        <name>shared</name>                        <value>                          <boolean>0</boolean>                        </value>                      </member>                      <member>                        <name>other_config</name>                        <value>                          <struct>                            <member>                              <name>i18n-original-value-name_description</name>                              <value>Physical DVD drives</value>                            </member>                            <member>                              <name>i18n-original-value-name_label</name>                              <value>DVD drives</value>                            </member>                            <member>                              <name>i18n-key</name>                              <value>local-hotplug-cd</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>tags</name>                        <value>                          <array>                            <data/>                          </array>                        </value>                      </member>                      <member>                        <name>sm_config</name>                        <value>                          <struct>                            <member>                              <name>type</name>                              <value>cd</value>                            </member>                          </struct>                        </value>                      </member>                      <member>                        <name>blobs</name>                        <value>                          <struct/>                        </value>                      </member>                    </struct>                  </value>                </member>              </struct>            </value>          </data>        </array>      </value>    </member>  </struct></value>"

## Taken from http://code.activestate.com/recipes/168639-progress-bar-class/
class ProgressBar:
    def __init__(self, min_value = 0, max_value = 100, width=77,**kwargs):
        self.char = kwargs.get('char', '#')
        self.mode = kwargs.get('mode', 'dynamic') # fixed or dynamic
        if not self.mode in ['fixed', 'dynamic']:
            self.mode = 'fixed'

        self.bar = ''
        self.min = min_value
        self.max = max_value
        self.span = max_value - min_value
        self.width = width
        self.amount = 0       # When amount == max, we are 100% done
        self.update_amount(0)


    def increment_amount(self, add_amount = 1):
        """
        Increment self.amount by 'add_ammount' or default to incrementing
        by 1, and then rebuild the bar string.
        """
        new_amount = self.amount + add_amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()


    def update_amount(self, new_amount = None):
        """
        Update self.amount with 'new_amount', and then rebuild the bar
        string.
        """
        if not new_amount: new_amount = self.amount
        if new_amount < self.min: new_amount = self.min
        if new_amount > self.max: new_amount = self.max
        self.amount = new_amount
        self.build_bar()

    def build_bar(self):
        """
        Figure new percent complete, and rebuild the bar string base on
        self.amount.
        """
        diff = float(self.amount - self.min)
        percent_done = int(round((diff / float(self.span)) * 100.0))

        # figure the proper number of 'character' make up the bar
        all_full = self.width - 2
        num_hashes = int(round((percent_done * all_full) / 100))

        if self.mode == 'dynamic':
            # build a progress bar with self.char (to create a dynamic bar
            # where the percent string moves along with the bar progress.
            self.bar = self.char * num_hashes
        else:
            # build a progress bar with self.char and spaces (to create a
            # fixe bar (the percent string doesn't move)
            self.bar = self.char * num_hashes + ' ' * (all_full-num_hashes)

        percent_str = str(percent_done) + "%"
        self.bar = '[ ' + self.bar + ' ] ' + percent_str


    def __str__(self):
        return str(self.bar)


class Xva(object):

    classProgressBar = None
    def __init__(self, memory="268435456", vcpus=1, name="Unnamed", classProgressBar=None):
        self.classProgressBar = classProgressBar
        self.disks = []
        self.vifs = []
        self.nextref = 9
        self.next_disk_letter = 1
        raw_xml = XML_DATA

        for olduuid in [ 'UUID1', 'UUID2', 'UUID3', 'UUID4', 'UUID5', 'UUID6' , 'UUID7', 'UUID8' ,'UUID9' ]:
            raw_xml = raw_xml.replace(olduuid, str(uuid()))



        self.tree = ET.fromstring(raw_xml)


        xml_objects = {}
        config_struct = xml_objects['config_struct'] = self.tree.findall("struct/member")[1].find("value")[0][0][0][0][2][1][0]
        config_members = xml_objects['config_members'] = config_struct.findall("member")
        xml_objects['VIFS_config'] = config_members[23].find("value").findall("array")
        xml_objects['VBD_config'] = config_members[24].find("value").findall("array")
        xml_objects['PV_bootloader'] = config_members[27].find("value")
        xml_objects['PV_kernel'] = config_members[28].find("value")
        xml_objects['PV_ramdisk'] = config_members[29].find("value")
        xml_objects['PV_args'] = config_members[30].find("value")
        xml_objects['memory_static_max'] = config_members[12].find("value")
        xml_objects['memory_dynamic_max'] = config_members[13].find("value")
        xml_objects['memory_dynamic_min'] = config_members[14].find("value")
        xml_objects['vcpus'] = config_members[18].find("value") 
        xml_objects['vcpus_max'] = config_members[17].find("value")
        xml_objects['HVM_boot_policy'] = config_members[33].find("value")
        xml_objects['nx'] = config_members[36][1][0][0][1].text
        xml_objects['acpi'] = config_members[36][1][0][1][1].text
        xml_objects['apic'] = config_members[36][1][0][2][1].text
        xml_objects['pae'] = config_members[36][1][0][3][1].text
        xml_objects['viridian'] = config_members[36][1][0][4][1].text
        xml_objects['name'] = config_members[4].find("value")
        xml_objects['first_vbd'] = self.tree.findall("struct/member")[1][1][0][0][2]
        xml_objects['first_vif'] = self.tree.findall("struct/member")[1][1][0][0][3][0]
        xml_objects['first_vdi'] = self.tree.findall("struct/member")[1][1][0][0][6]
        xml_objects['objects_array'] =  self.tree.findall("struct/member")[1][1][0][0]
        

        self.xml_objects = xml_objects

        self.set_memory(memory) 
        self.set_vcpus(vcpus) 
        self.set_name(name)






    def new_ref(self):
        tmp = self.nextref
        self.nextref = self.nextref + 1
        return "Ref:%d" % tmp


    def set_nx(self, value):

        if value:
            self.xml_objects['nx'] = "true"

        else:
            self.xml_objects['nx'] = "false"


    def set_acpi(self, value):

        if value:
            self.xml_objects['acpi'] = "true"

        else:
            self.xml_objects['acpi'] = "false"

    def set_apic(self, value):

        if value:
            self.xml_objects['apic'] = "true"

        else:
            self.xml_objects['apic'] = "false"

    def set_pae(self, value):

        if value:
            self.xml_objects['pae'] = "true"

        else:
            self.xml_objects['pae'] = "false"

    def set_viridian(self, value):

        if value:
            self.xml_objects['viridian'] = "true"

        else:
            self.xml_objects['viridian'] = "false"

    def print_report(self):

        print "VM Details:"

        print "Name: %s" % self.xml_objects['name'].text
        if self.xml_objects['HVM_boot_policy'].text == "BIOS order":
            print "Type: HVM"
            hvm=True
        else:
            print "Type: Paravirtualised"
            hvm=False
        print "VCPUS: %s" % self.xml_objects['vcpus'].text
        print "Memory(bytes): %s" % self.xml_objects['memory_static_max'].text
        print "ACPI: %s" % self.xml_objects['acpi']
        print "APIC: %s" % self.xml_objects['apic']
        print "PAE: %s" % self.xml_objects['pae']
        print "NX: %s" % self.xml_objects['nx']
        print "Viridian: %s" % self.xml_objects['viridian']

        
        iteration = 0
        for disk in self.disks:
            if iteration == 0:
               if hvm:
                   print "Disk 0(Bootable): %s" % disk[1]
               else:
                   print "Disk xvda(Bootable): %s" % disk[1]
                   

            else:
               if hvm: 

                   print "Disk %d: %s" % ( iteration , disk[1])

               else:
                   print "Disk xvd%c: %s" % ( iteration + 97, disk[1])
               


            iteration = iteration + 1
            




    def add_disk(self, path):
        input_file = open(path, "rb") 
        input_file.seek(0,os.SEEK_END)
        size = input_file.tell()
        if len(self.disks) == 0:
            self.xml_objects['first_vdi'][0][2][1][0][8][1].text = str(size)
            self.xml_objects['first_vdi'][0][2][1][0][9][1].text = str(size)

            ref = self.xml_objects['first_vdi'][0][1][1].text
            disk = (ref, path , size)
            self.disks.append(disk)
        else:
            ## copy a new vbd
            new_vbd_ref = self.new_ref()
            new_vdi_ref = self.new_ref()

            ## copy a new vbd

            new_vbd = copy.deepcopy(self.xml_objects['first_vbd'])
            ## Ref
            new_vbd[0][1][1].text = new_vbd_ref
            ## UUID

            new_vbd[0][2][1][0][0][1].text = str(uuid())


            ## Map the VDI ref 

            new_vbd[0][2][1][0][4][1].text = new_vdi_ref

            ## Set disk letter and userdevice

            new_vbd[0][2][1][0][5][1].text  = "xvd%s" % chr(self.next_disk_letter + 97)

            new_vbd[0][2][1][0][6][1].text = str(self.next_disk_letter)
            ## bootable to false
            new_vbd[0][2][1][0][7][1][0].text = "0"




            ## copy a new vdi
            new_vdi = copy.deepcopy(self.xml_objects['first_vdi'])
            ## map the VBD ref
            new_vdi[0][2][1][0][6][1][0][0][0].text = new_vbd_ref
            ## uuid
            new_vdi[0][2][1][0][0][1].text = str(uuid())
            ## ref
            new_vdi[0][1][1].text = new_vdi_ref

            new_vdi[0][2][1][0][8][1].text = str(size)
            new_vdi[0][2][1][0][9][1].text = str(size)


            ## name label

            new_vdi[0][2][1][0][1][1].text = str(self.next_disk_letter)

            disk = (new_vdi_ref, path , size)
            

            self.disks.insert(len(self.disks) -1,disk)
         

            self.xml_objects['objects_array'].append(new_vbd)
            self.xml_objects['objects_array'].append(new_vdi)

            new_vbd_value = copy.deepcopy(self.xml_objects['VBD_config'][0][0][0])

            new_vbd_value.text = new_vbd_ref

            self.xml_objects['VBD_config'][0][0].append(new_vbd_value)
             
            self.next_disk_letter = self.next_disk_letter + 1

            if self.next_disk_letter  == 3:
                self.next_disk_letter = self.next_disk_letter + 1
            


        


    def is_hvm(self):
        self.xml_objects['HVM_boot_policy'].text = "BIOS order"

    def is_pv(self):
        self.xml_objects['HVM_boot_policy'].text = ""
        self.xml_objects['PV_bootloader'].text = "pygrub"



    def set_name(self, name):
        self.xml_objects['name'].text = name

    def get_name(self):
        return self.xml_objects['name'].text



    def set_memory(self, memory):
        self.xml_objects['memory_static_max'].text = str(memory)
        self.xml_objects['memory_dynamic_max'].text = str(memory)
        self.xml_objects['memory_dynamic_min'].text = str(memory)


    def get_memory(self):

        return self.xml_objects['memory_static_max'].text

    def set_name(self, name):
        self.xml_objects['name'].text = name

    def get_name(self):
        return self.xml_objects['name'].text

    def set_vcpus(self, vcpus):
        self.xml_objects['vcpus'].text = str(vcpus)
        self.xml_objects['vcpus_max'].text = str(vcpus)

    def get_vcpus(self):

        return self.xml_objects['vcpus'].text


    def handle_exception(self):

        ## this is for when the http connection drops, we try to figure out what happened.

        if self.conn:
            try:
                response = self.conn.getresponse()

            except:
                print "Internal Error. Possible problem: Please make sure you have enough space on your default SR"
                sys.exit(254)



            if response.status == 401:
                print "Unauthorised response from server. Exiting"
                sys.exit(254)
            elif response.status != 200:
                print "Server returned error code %d. Exiting" % response.status
                print "Extra Info: %s" % response.read()
                sys.exit(254)



        else:

            print "Error writing file. Exiting"
            sys.exit(254)


    def save_as(self, filename=None, sparse=False, username=None, password=None,
         server=None, ssl=True):

         
        self.print_report()
        
        if server:
            print "Connecting to target %s" % server
            import base64
            auth = base64.encodestring("%s:%s" % (username, password)).strip()
            

            import httplib
            if ssl:
                conn = httplib.HTTPSConnection(server)
            else:
                conn = httplib.HTTPConnection(server)
            headers = {"Authorization" : "Basic %s" % auth}
            conn.request("PUT", "/import", headers=headers)
            conn.write = conn.send
            self.conn = conn
            output_file = tarfile.open(fileobj=conn, mode='w|')
            
        
        else:
            output_file = tarfile.open(filename, mode='w|')
            print "Generating XVA file %s" % filename



        info = tarfile.TarInfo(name="ova.xml")
        output_xml = ET.tostring(self.tree)

        string = cStringIO.StringIO(output_xml)
        string.seek(0)

        info.size=len(output_xml)

        try:
            output_file.addfile(tarinfo=info, fileobj=string)

        except:
            
            self.handle_exception()
                
        
        
        chunksize=1048576


        for disk in self.disks:
            basefilename=0
            input_file = open(disk[1], "rb")
            input_file.seek(0,os.SEEK_END)
            input_file_size=input_file.tell()
            input_file.seek(0)



            position = 0
            print "\nProcessing disk %s(%s bytes)" % (disk[1], input_file_size)
            read_len = -1
            if self.classProgressBar == None:
                prog = ProgressBar(0, input_file_size, 77, mode='fixed')
            else:
                prog = self.classProgressBar
            oldprog = str(prog)
            while True:
                input_buffer = input_file.read(chunksize)
                read_len = len(input_buffer)
                if read_len == 0 : break 
                force = False
                 
                if position == 0: force=True

                if (input_file_size - position) < (chunksize * 2) : force = True

                position = position + chunksize
                if self.classProgressBar == None:
                    prog.update_amount(position)
                else:
                    prog.update_amount(float(position)/float(input_file_size))

                if oldprog != str(prog):
                    print prog, "\r",
                    sys.stdout.flush()
                    oldprog=str(prog)
                input_file.seek(position)



                zeroes = input_buffer.count('\0')

                if zeroes == chunksize and not force and sparse:
                    
                    basefilename = basefilename + 1
                
                else:
                


                    string = cStringIO.StringIO(input_buffer)
                    string.seek(0)
                    info = tarfile.TarInfo(name="%s/%08d" % (disk[0] , basefilename))
                    info.size=read_len
                    
                    try:
                        output_file.addfile(tarinfo=info, fileobj=string)
                    except:
                        self.handle_exception()

                    hash = sha1(input_buffer).hexdigest()
                    string = cStringIO.StringIO(hash)
                    info = tarfile.TarInfo(name="%s/%08d.checksum" % (disk[0], basefilename))
                    info.size=40

                    try:
                        output_file.addfile(tarinfo=info, fileobj=string)
                    except:
                        self.handle_exception()

                    basefilename = basefilename + 1
        print "\n"
        sys.stdout.flush()
        output_file.close()
        if self.classProgressBar:
            prog.finish()

        if server:
            response = conn.getresponse()
            if response.status == 200:
                if self.classProgressBar == None:
                    print "VM Successfully streamed"
                else:
                    prog.update_text("VM Successfully streamed")
            else:
                if self.classProgressBar == None:
                    print "VM did not stream successfully, Return code: %d" % response.status
                else:
                    prog.update_text("VM did not stream successfully, Return code: %d" % response.status)


if __name__ == "__main__":

    from optparse import OptionParser
    from optparse import OptionGroup

    
    parser = OptionParser()



    parser.add_option("-c", "--config",  dest="config",default=None, help="Specify the OSS Xen config file to process(all other options except -o are ignored)", metavar="FILE")
    parser.add_option("--sparse", action="store_true", dest="sparse", help="Attempt sparse mode(detecting chunks that are zero)", default=False)

    params = OptionGroup(parser, "Virtual Machine Parameters",
                    "These options are only read when you dont specify a config file with -c")




    params.add_option("-d", "--disk", action="append", dest="disks", help="Add disk in file/block device DISK, make sure first disk given is the boot disk", metavar="DISK")
    params.add_option("-m", "--memory",  dest="memory", default=256,  type="int",  help="Set memory to MEM(Megabytes), default 256", metavar="MEM")
    params.add_option("-n", "--name",  dest="name", default="Unnamed",   help="Set VM name to NAME(default unnamed)", metavar="NAME")
    params.add_option("-v", "--vcpus",  dest="vcpus", default=1, type="int", help="Set VCPUS to NUM(default 1)", metavar="NUM")
    params.add_option("--no-acpi", action="store_true", dest="noacpi", help="ACPI Disabled", default=False)
    params.add_option("--no-apic", action="store_true", dest="noapic", help="APIC Disabled", default=False)
    params.add_option("--no-viridian", action="store_true", dest="noviridian", help="Viridian Disabled", default=False)
    params.add_option("--no-pae", action="store_true", dest="nopae", help="PAE Disabled", default=False)
    params.add_option("--nx", action="store_true", dest="nx", help="NX enabled(default no)", default=False)
    params.add_option("--is-hvm", action="store_true", dest="hvm", help="Is HVM VM(defaults to HVM)", default=True)
    params.add_option("--is-pv", action="store_false", dest="hvm", help="Is PV VM")

    parser.add_option_group(params)

    output_options = OptionGroup(parser, "Output Options", "These are the options that dictates where the VM should be saved or streamed to a server. You can either save to a file or stream to a server, not both. "
    "One of either -o or -s have to be specified")

    output_options.add_option("-f", "--filename", dest="filename", help="Save XVA to file FILE", metavar="FILE", default=None)
    output_options.add_option("-s", "--server", dest="server", help="Stream VM to host HOSTNAME", metavar="HOSTNAME", default=None)
    output_options.add_option("--username", dest="username", help="Use username USERNAME when streaming to remote host", metavar="USERNAME")
    output_options.add_option("--password", dest="password", help="Use password PASSWORD when streaming to remote host", metavar="PASSWORD")
    output_options.add_option("--no-ssl", action="store_true", dest="nossl", help="SSL disabled with streaming", default=False)


    parser.add_option_group(output_options)

    (options, args) = parser.parse_args()

    if not options.server and not options.filename:
        parser.error("Please specify either a filename or server")

    if options.server and (not options.username or not options.password):
        parser.error("Please specify a username and password when streaming")
           


    machine = Xva()

    if options.config:
        params = {}
        execfile(options.config,params)
        if params.has_key("name"): machine.set_name( params['name'] )
        if params.has_key("vcpus"): machine.set_vcpus( params['vcpus'] )
        if params.has_key('kernel'):
            if params['kernel'].endswith("hvmloader"):
                machine.is_hvm()
            else:
                print "Kernels that are loaded from the Dom0 aren't supported. Use pygrub"
                sys.exit(255)
        else:
            machine.is_pv()

        if params.has_key("disk") and len(params['disk']) != 0:

            for disk in params['disk']:

                (path, device, mode) = disk.split(",")
                path_split = path.split(":")
                path_split.reverse()
                machine.add_disk(path_split[0])
                
 
        else:
 
           print "You need at least 1 Disk, Exiting"
           sys.exit(254)

        

        if params.has_key("memory"):
            try:
                memory = int(params['memory'] )
                machine.set_memory( memory * 1024 * 1024)
            except:
                print "Could parse memory, setting to 256M"
                machine.set_memory(268435456)
                
        if params.has_key("apic") and params['apic'] == 0:
            machine.set_apic(False)
        if params.has_key("acpi") and params['acpi'] == 0:
            machine.set_acpi(False)
        if params.has_key("nx") and params['nx'] == 1:
            machine.set_nx(options.nx)
        if params.has_key("pae") and params['pae'] == 0:
            machine.set_pae(False)

        

            
            

    else:
    	if options.disks:    
       	    for disk in options.disks: machine.add_disk(disk)
 
        else:
            parser.error("At least one disk needs to be specified")
  
    
        if options.hvm:
            machine.is_hvm()
        else:
            machine.is_pv()

        machine.set_name(options.name)
        machine.set_vcpus(options.vcpus)
        machine.set_acpi(not options.noacpi)
        machine.set_apic(not options.noapic)
        machine.set_nx(options.nx)
        machine.set_viridian(not options.noviridian)
        machine.set_pae(not options.nopae)

        memory = (options.memory * 1024 * 1024)
        machine.set_memory(memory)
    

    if options.filename:    
        machine.save_as(filename=options.filename, sparse=options.sparse)
    else:
        machine.save_as(server=options.server, username=options.username,
               password=options.password, ssl= not options.nossl,  sparse=options.sparse)
        



