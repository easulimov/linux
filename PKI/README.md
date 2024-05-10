# Описывается пример создание своего центра сертификации
Источники:
https://github.com/ilyabobrusev/alpha/blob/master/alpha/ssl%20tls/commands.txt
https://www.opennet.ru/base/sec/openssl.txt.html
https://ispserver.ru/help/open-ssl-commands
https://sysos.ru/archives/668#i-4
https://sgolubev.ru/openssl-ca/

### Подготовка директорий

| Директория | Описание |
|------------|-----------|
| certs | Cодержит сертификаты, сгенерированные и подписанные ЦС. |
| crl | Каталог списка отзыва сертификатов (CRL) содержит списки отзыва сертификатов, сгенерированные ЦС. |
| newcerts | В этом каталоге хранится копия каждого сертификата, подписанного ЦС, с серийным номером сертификата в качестве имени файла. |
| private | Этот каталог содержит закрытые ключи для ЦС, включая закрытые ключи корневого ЦС и промежуточного ЦС. Эти ключи используются для подписи сертификатов и CRL. |
| csr | В этом каталоге хранится копия каждого запроса сертификата. |
<br>

```bash
mkdir -p /root/ca/{certs,crl,newcerts,private,csr}
```
<br>

```bash
cd /root/ca
chmod 700 private
touch index
touch serial
touch crlnumber
openssl rand -hex 20 > serial
echo 00 > crlnumber
```
<br>

| Файл | Описание |
|------------|-----------|
| index | Выступает в качестве плоской базы для отслеживания выписанных сертификатов. |
| serial | 	Используется для отслеживания последнего серийного номера, который был использован для выдачи сертификата. Важно, чтобы никогда не было выдано двух сертификатов с одинаковым серийным номером от одного и того же ЦС.|
| crlnumber | Содержит текущий номер CRL. Номер CRL — это уникальное целое число, которое увеличивается каждый раз при создании нового списка отзыва сертификатов (CRL). Это помогает отслеживать последние CRL, выданные ЦС, и гарантировать, что CRL выдаются в надлежащей последовательности. |
<br>

```bash
mkdir -p /root/ca/intermediate/{certs,crl,csr,newcerts,private}
```
<br>

```bash
cd /root/ca/intermediate
chmod 700 private
touch index
touch serial
touch crlnumber
openssl rand -hex 20 > serial
echo 00 > crlnumber
```
<br>

### ROOT CA
#### Создание когнфигурационного файла для ROOT CA
Требуется создать файл с конфигурацией 
```bash
cd /root/ca
vim /root/ca/openssl-root.cnf
```
<br>
Содержимое файла ***/root/ca/openssl-root.cnf***

```ini
[ ca ]
#
# OpenSSL configuration for the Root Certification Authority.
#

[ ca ]
default_ca = CA_default

[ CA_default ]
# Directory and file locations.
dir               = /root/ca/
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

# The root key and root certificate.
private_key       = $dir/private/rootca.key
certificate       = $dir/certs/rootca.crt

# For certificate revocation lists.
crlnumber         = $dir/crlnumber
crl               = $dir/crl/rootca.crl
crl_extensions    = crl_ext
default_crl_days  = 182

default_md        = sha256

name_opt          = ca_default
cert_opt          = ca_default

default_days      = 7300
default_md        = sha256

preserve          = no
unique_subject    = no

policy            = policy_strict

# For the CA policy
[ policy_strict ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = 2048
distinguished_name  = req_distinguished_name
string_mask         = utf8only

default_md          = sha256
default_keyfile     = private/rootca.key

x509_extensions     = v3_ca

[ req_distinguished_name ]
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name (full name)
localityName                    = Locality Name (eg, city)
organizationName                = Organization Name (eg, company)
organizationalUnitName          = Organizational Unit Name (eg, section)
commonName                      = Common Name (eg, your name or your server hostname)
emailAddress                    = Email Address

# Optionally, specify some defaults.  
countryName_default             = RU
stateOrProvinceName_default     = Moscow
localityName_default            = Moscow
organizationName_default       = SEA_TEST_ORG
organizationalUnitName_default  = IT
emailAddress_default            = admin@sea.local

[ v3_ca ]
subjectKeyIdentifier     = hash
authorityKeyIdentifier   = keyid:always,issuer
basicConstraints         = critical, CA:true
keyUsage                 = critical, digitalSignature, cRLSign, keyCertSign

[ v3_intermediate_ca ]
subjectKeyIdentifier     = hash
authorityKeyIdentifier   = keyid:always,issuer

# As pathlen restricts creating any further intermidiate CA in the chain.
basicConstraints         = critical, CA:true, pathlen:0
keyUsage                 = critical, digitalSignature, cRLSign, keyCertSign
crlDistributionPoints    = crldp1_section

[ crl_ext ]
# CRL extensions.
authorityKeyIdentifier   = keyid:always,issuer

[ crldp1_section ]
fullname                 = URI:http://ca.sea.local/rootca.crl
```
<br>

#### Создание private key для ROOT CA

```bash
cd /root/ca
openssl genrsa -aes256 -out private/rootca.key 4096
```
<br>

Команда openssl предполагает установки парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

```bash
chmod 400 private/rootca.key
```
<br>

#### Создание сертификата для ROOT CA

```bash
cd /root/ca
openssl req -config openssl-root.cnf -key private/rootca.key -new -x509 -days 7300 -rand_serial -sha256 -extensions v3_ca -out certs/rootca.crt
```
<br>

Команда openssl предполагает установки парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

Также, потребуется указать/переопределить умолчания из openssl.cnf:
```
# Optionally, specify some defaults.  
countryName_default             = RU
stateOrProvinceName_default     = Moscow
localityName_default            = Moscow
organizationName_default       = SEA_TEST_ORG
organizationalUnitName_default  = IT
emailAddress_default            = admin@sea.local
```
<br>

Например:
```
openssl req -config openssl-root.cnf -key private/rootca.key -new -x509 -days 7300 -rand_serial -sha256 -extensions v3_ca -out certs/rootca.crt
-----
Country Name (2 letter code) [XX]: RU
State or Province Name []: Moscow
Locality Name []:Moscow
Organization Name []: SEA_TEST_ORG
Organizational Unit Name []:IT
Common Name []: RootCA SEA
Email Address []: admin@sea.local
```
<br>

```bash
chmod 444 certs/rootca.crt
```
<br>

#### Проверка ROOT CA
```bash
openssl x509 -noout -text -in certs/rootca.crt
```
<br>

#### Списки отзывов сертификатов 

Создать начальный, хоть и пустой CRL корневого ЦС:
```bash
openssl ca -config openssl-root.cnf -gencrl -out crl/rootca.crl
```
<br>

Вывести информацию о списке отзыва:
```bash
openssl crl -in crl/rootca.crl -text -noout
```
<br>


### INTERMEDIATE CA
#### Создание конфигурационного файла для INTERMEDIATE CA

Требуется создать файл с конфигурацией 
```bash
vim /root/ca/intermediate/openssl-intermediate.cnf
```
<br>
Содержимое файла ***/root/ca/intermediate/openssl-intermediate.cnf***

```ini
#
# OpenSSL configuration for the Intermediate Certification Authority.
#

[ ca ]
default_ca = CA_default

[ CA_default ]
# Directory and file locations.
dir               = /root/ca/intermediate
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

# The root key and root certificate.
private_key       = $dir/private/intermediateca.key
certificate       = $dir/certs/intermediateca.crt

# For certificate revocation lists.
crlnumber         = $dir/crlnumber
crl               = $dir/crl/intermediateca.crl
crl_extensions    = crl_ext
default_crl_days  = 30

default_md        = sha256

name_opt          = ca_default
cert_opt          = ca_default

default_days      = 3650
default_md        = sha256

preserve          = no
unique_subject    = no

policy            = policy_strict

# For the CA policy
[ policy_strict ]
countryName                = optional
stateOrProvinceName        = optional
organizationName           = optional
organizationalUnitName     = optional
commonName                 = supplied
emailAddress               = optional

# For the 'anything' policy
# At this point in time, you must list all acceptable 'object' types.
[ policy_anything ]
countryName                = optional
stateOrProvinceName        = optional
localityName               = optional
organizationName           = optional
organizationalUnitName     = optional
givenName                  = optional
commonName                 = supplied
emailAddress               = optional
title                      = optional

[ req ]
default_bits        = 2048
distinguished_name  = req_distinguished_name
string_mask         = utf8only

default_md          = sha256
default_keyfile     = private/intermediateca.key

req_extensions      = req_ext
x509_extensions     = v3_intermediate_ca

[ req_distinguished_name ]
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name (full name)
localityName                    = Locality Name (eg, city)
organizationName                = Organization Name (eg, company)
organizationalUnitName          = Organizational Unit Name (eg, section)
commonName                      = Common Name (eg, your name or your server hostname)
emailAddress                    = Email Address

# Optionally, specify some defaults.  
countryName_default             = RU
stateOrProvinceName_default     = Moscow
localityName_default            = Moscow
organizationName_default       = SEA_TEST_ORG
organizationalUnitName_default  = IT
emailAddress_default            = admin@sea.local

[ req_ext ]
basicConstraints         = critical, CA:true
keyUsage                 = critical, digitalSignature, cRLSign, keyCertSign

[ v3_intermediate_ca ]
subjectKeyIdentifier     = hash
authorityKeyIdentifier   = keyid:always,issuer

# As pathlen restricts creating any further intermidiate CA in the chain.
basicConstraints         = critical, CA:true, pathlen:0
keyUsage                 = critical, digitalSignature, cRLSign, keyCertSign
crlDistributionPoints    = crldp1_section

[ crl_ext ]
# CRL extensions.
authorityKeyIdentifier   = keyid:always

[ crldp1_section ]
fullname                 = URI:http://ca.sea.local/intermidiateca.crl

[ ocsp ]
basicConstraints         = CA:FALSE
subjectKeyIdentifier     = hash
authorityKeyIdentifier   = keyid,issuer
keyUsage                 = critical, digitalSignature
extendedKeyUsage         = critical, OCSPSigning
```
<br>

#### Создание private key для INTERMEDIATE CA

```bash
cd /root/ca
openssl genrsa -aes256 -out intermediate/private/intermediateca.key 4096
```
<br>

Команда openssl предполагает установки парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

```bash
chmod 400 intermediate/private/intermediateca.key
```
<br>

#### Создание CSR(certificate signing request) для INTERMEDIATE CA

```bash
cd /root/ca
openssl req -config intermediate/openssl-intermediate.cnf -new -sha256 -key intermediate/private/intermediateca.key -out intermediate/csr/intermediateca.csr
```
<br>

Команда openssl предполагает установку парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

Также, потребуется указать/переопределить умолчания из openssl-intermediate.cnf:
```
# Optionally, specify some defaults.  
countryName_default             = RU
stateOrProvinceName_default     = Moscow
localityName_default            = Moscow
organizationName_default       = SEA_TEST_ORG
organizationalUnitName_default  = IT
emailAddress_default            = admin@sea.local
```
<br>

Например:
```
openssl req -config intermediate/openssl-intermediate.cnf -new -sha256 -key intermediate/private/intermediateca.key -out intermediate/csr/intermediate.csr
-----
Country Name (2 letter code) [XX]: RU
State or Province Name []: Moscow
Locality Name []:Moscow
Organization Name []: SEA_TEST_ORG
Organizational Unit Name []:IT
Common Name []: IntermediateCA SEA
Email Address []: admin@sea.local
```
<br>

Проверка csr запроса:
```
openssl req -in intermediate/csr/intermediateca.csr -noout -text -reqopt no_version,no_pubkey,no_sigdump
```
<br>

#### Создание сертификата для INTERMEDIATE CA

```bash
cd /root/ca
openssl ca -config openssl-root.cnf -extensions v3_intermediate_ca -days 3650 -rand_serial -notext -md sha256 -in intermediate/csr/intermediateca.csr -out intermediate/certs/intermediateca.crt
```
<br>

Команда openssl предполагает установку парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

```bash
chmod 444 intermediate/certs/intermediateca.crt
```
<br>

#### Проверка сертификата для INTERMEDIATE CA

```bash
openssl x509 -noout -text -in intermediate/certs/intermediateca.crt
```
<br>

```bash
openssl verify -CAfile certs/rootca.crt intermediate/certs/intermediateca.crt
```
<br>

#### Создание цепочки корневых сертификатов

```bash
cat intermediate/certs/intermediateca.crt certs/rootca.crt > intermediate/certs/cachain.crt
```
<br>

```bash
chmod 444 intermediate/certs/cachain.crt
```
<br>

#### Списки отзывов сертификатов 

Создать начальный, хоть и пустой CRL корневого ЦС:
```bash
cd /root/ca
openssl ca -config intermediate/openssl-intermediate.cnf -gencrl -out intermediate/crl/intermediateca.crl
```
<br>

Вывести информацию о списке отзыва:
```bash
openssl crl -in intermediate/crl/intermediateca.crl -text -noout
```
<br>

### Создание сертификата для сервера
#### Создание конфигурационного файла для серверного сертификата

> Внимание! Пример для теста, небезопасно указывать в SAN localhost и 127.0.0.1 Также, стоит избегать использования wildcard
<br>

```bash
cd /root/ca
vim intermediate/sea.local.cnf
```
<br>

Содержимое файла ***/root/ca/intermediate/sea.local.cnf***
```ini
[ req ]
default_bits        = 2048
default_md          = sha256
string_mask         = utf8only
x509_extensions     = req_ext
distinguished_name  = req_distinguished_name
prompt = no

[ req_distinguished_name ]
C = RU
ST = Moscow
L = Moscow
CN = sea.local

# Common paramets
# C   = Country Name (2 letter code) - AE
# ST  = State or Province Name (full name) - Emirate of Dubai
# L   = Locality Name (eg, city) - Dubai
# O   = Organization Name - NORD RIM
# OU  = Organizational Unit Name (eg, section) - IT
# CN  = Common Name (eg, your name or your server\'s hostname)

[ req_ext ]
basicConstraints        = CA:FALSE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid,issuer
keyUsage                = digitalSignature, keyEncipherment
extendedKeyUsage        = serverAuth, clientAuth
subjectAltName          = @alt_names
crlDistributionPoints   = crldp1_section

[ crldp1_section ]
fullname = URI:http://ca.sea.local/intermediateca.crl

[alt_names]
DNS.1 = localhost
DNS.2 = sea.local
DNS.3 = *.sea.local
IP.1 = 127.0.0.1
```
<br>

#### Создание private key

```bash
cd /root/ca
openssl genrsa -out intermediate/private/sea.local.key 2048
```
<br>

```bash
chmod 400 intermediate/private/sea.local.key
```
<br>

#### Создание CSR(certificate signing request) для серверного сертификата

```bash
openssl req -config intermediate/sea.local.cnf -extensions req_ext -new -sha256 -key intermediate/private/sea.local.key -out intermediate/csr/sea.local.csr
```
<br>

#### Создание серверного сертификата

```bash
openssl ca -batch -config intermediate/openssl-intermediate.cnf -extfile intermediate/sea.local.cnf -extensions req_ext -days 365 -rand_serial -notext -in intermediate/csr/sea.local.csr -out intermediate/certs/sea.local.crt
```
<br>

```bash
chmod 444 intermediate/certs/sea.local.crt
```
<br>

 #### Проверка сертификата

```bash
openssl x509 -noout -text -in intermediate/certs/sea.local.crt
```
<br>

```bash
openssl verify -CAfile intermediate/certs/cachain.crt \
intermediate/certs/sea.local.crt
```
<br>



