### Test enviroment with 5 VMs based on centos7

---
#### Sending data to PushGateway (example)
```
cat <<EOF | curl --data-binary @- http://127.0.0.1:9091/metrics/job/sea_test_job/instance/sea_test_srv
# TYPE sea_edu_counter counter
sea_edu_counter{type="counter"} 11
# TYPE sea_gauge gauge
sea_gauge 777.283
EOF
```
