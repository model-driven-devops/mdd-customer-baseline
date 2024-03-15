# Creating Jinja Templates

This assumes the following:
- You have MDD set up and you are running it locally.
- You have a test device that is accessible.
- You have NSO running with the ability to connect to your test device.

## Initial Harvest
First, you need to modify your mdd.yml file found under inventory -> group_vars -> all. You want to comment out "-oc" in mdd_data_types. This will force NSO to harvest the native NED data.

```
mdd_data_types:
  # - oc
  - config
```

If you haven't already synced your device with NSO, you can go to the general MDD instructions located here: https://github.com/model-driven-devops/mdd/blob/main/exercises/deploy-topology.md
This will list the playbooks you can use to onboard your test device.

Next, do an initial harvest

```
ansible-playbook ciscops.mdd.harvest
```

If you have multiple devices in inventory, you can do a --limit= to target one device. This will generate your baseline configuration represented as a YANG model and place it under your mdd-data directory.

example
```
mdd_data:
  config:
    tailf-ned-cisco-ios:hostname: mdd-router-test
    tailf-ned-cisco-ios:tailfned:
      police: cirmode
    tailf-ned-cisco-ios:version: '17.9'
    tailf-ned-cisco-ios:service:
      conf:
        pad: false
      tcp-keepalives-in:
      - null
      tcp-keepalives-out:
      - null
      timestamps:
        debug:
          datetime: {}
        log:
          datetime: {}
      password-encryption: {}
      linenumber:
      - null
      call-home:
      - null
    tailf-ned-cisco-ios:login:
      on-failure:
        log:
        - null
      on-success:
        log:
        - null
```

## Pick a template

This assumes you are familiar with the customer directory, so to avoid putting customer specefic data here, I will try to be general. The main templates are located under root -> system -> xxxxConfDtl -> Network Library. 
You can select an architcture directory under ConfDtl and then select a device template that should look like Project-U00-device_type-etc.txt. These device templates will list what general templates are used to create the final configuration.

For example, a router template will list the requied sub template such as OSPF, VLANs, Interfaces, etc.

Example
```
Copy the following templates from the Network Library System Installation and Configuration
!# document and paste to the appropriate sections:
!# 1. [ROUTER_BASELINE]
!#    - Configure the HW baseline.
!# 2. [COPP_BASELINE]
!#    - Configure enterprise control plane policy.
!# 3. [NON-SWITCHPORT_L3_BASELINE]
!#    - Configure the non-switchport interface baseline for all device interfaces.
!# 4. [VRF_DEFINITION]
!#    - Configure the core VRF.
!#    - Configure the management VRF.
!# 5. [LOOPBACK_INTERFACE]
!#    - Configure loopback10 interface.
!# 6. [ROUTED_INTERFACE]
!#    - Configure the interface.
!# 7. [OSPF_BASELINE]
!#    - Configure the OSPF baseline.
!# 8. [OSPF_NETWORK]
!#    - Configure the OSPF network statements.
!# 9. [VRF_STATIC_ROUTE]
!#    - Configure management VRF static route.
```
