{% for vol in grains['ebs_mounts'] %}  

# Mount the device to the given mount point, but first
# make sure the device exists. AWS requires the device
# to be defined like sdj, but in modern kernels the
# device will be remapped to xvdj.

# look up the device name using our nifty find_ebs_device method
# in our extended mount module
{% set device_name=salt['mount.find_ebs_device'](vol['device']) %}

{% if device_name %}
{{ vol['mount_point'] }}:
  mount:
    - mounted
    - device: {{ device_name }}
    - fstype: {{ vol['fs_type'] }}
    - mkmnt: True
{% endif %}

{% endfor %}