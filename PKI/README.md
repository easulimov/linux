# Описывается пример создание своего центра сертификации
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

default_days      = 3650
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
chmod 400 private/rootca.key.pem
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
chmod 444 certs/ca.cert.pem
```
<br>

#### Проверка ROOT CA
```bash
openssl x509 -noout -text -in certs/ca.cert.pem
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
vim /root/ca/intermediate/openssl.cnf
```
<br>
Содержимое файла ***/root/ca/intermediate/openssl.cnf***

```ini
# OpenSSL intermediate CA configuration file.
# Copy to `/root/ca/intermediate/openssl.cnf`.

[ ca ]
# `man ca`
default_ca = CA_default

[ CA_default ]
# Directory and file locations.
dir               = /root/ca/intermediate
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

# The root key and root certificate.
private_key       = $dir/private/intermediate.key.pem
certificate       = $dir/certs/intermediate.cert.pem

# For certificate revocation lists.
crlnumber         = $dir/crlnumber
crl               = $dir/crl/intermediate.crl.pem
crl_extensions    = crl_ext
default_crl_days  = 30

# SHA-1 is deprecated, so use SHA-2 instead.
default_md        = sha256

name_opt          = ca_default
cert_opt          = ca_default
default_days      = 375
preserve          = no
policy            = policy_loose

[ policy_strict ]
# The root CA should only sign intermediate certificates that match.
# See the POLICY FORMAT section of `man ca`.
countryName             = match
stateOrProvinceName     = match
organizationName        = match
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ policy_loose ]
# Allow the intermediate CA to sign a more diverse range of certificates.
# See the POLICY FORMAT section of the `ca` man page.
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
# Options for the `req` tool (`man req`).
default_bits        = 2048
distinguished_name  = req_distinguished_name
string_mask         = utf8only

# SHA-1 is deprecated, so use SHA-2 instead.
default_md          = sha256

# Extension to add when the -x509 option is used.
x509_extensions     = v3_ca

[ req_distinguished_name ]
# See <https://en.wikipedia.org/wiki/Certificate_signing_request>.
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name
localityName                    = Locality Name
0.organizationName              = Organization Name
organizationalUnitName          = Organizational Unit Name
commonName                      = Common Name
emailAddress                    = Email Address

# Optionally, specify some defaults.  
countryName_default             = RU
stateOrProvinceName_default     = Moscow
localityName_default            = Moscow
0.organizationName_default        = SEA_TEST_ORG
organizationalUnitName_default  = IT
emailAddress_default            = admin@sea.local

[ v3_ca ]
# Extensions for a typical CA (`man x509v3_config`).
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[ v3_intermediate_ca ]
# Extensions for a typical intermediate CA (`man x509v3_config`).
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:0
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[ usr_cert ]
# Extensions for client certificates (`man x509v3_config`).
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection

[ server_cert ]
# Extensions for server certificates (`man x509v3_config`).
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[ crl_ext ]
# Extension for CRLs (`man x509v3_config`).
authorityKeyIdentifier=keyid:always

[ ocsp ]
# Extension for OCSP signing certificates (`man ocsp`).
basicConstraints = CA:FALSE
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = critical, digitalSignature
extendedKeyUsage = critical, OCSPSigning
```
<br>

#### Создание private key для INTERMEDIATE CA

```bash
cd /root/ca
openssl genrsa -aes256 -out intermediate/private/intermediate.key.pem 4096
```
<br>

Команда openssl предполагает установки парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

```bash
chmod 400 intermediate/private/intermediate.key.pem
```
<br>

#### Создание CSR(certificate signing request) для INTERMEDIATE CA

```bash
cd /root/ca
openssl req -config intermediate/openssl.cnf -new -sha256 -key intermediate/private/intermediate.key.pem -out intermediate/csr/intermediate.csr.pem
```
<br>

Команда openssl предполагает установку парольной фразы на ключ:
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
openssl req -config intermediate/openssl.cnf -new -sha256 -key intermediate/private/intermediate.key.pem -out intermediate/csr/intermediate.csr.pem
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

#### Создание сертификата для INTERMEDIATE CA

```bash
cd /root/ca
openssl ca -config openssl.cnf -extensions v3_intermediate_ca -days 3650 -notext -md sha256 -in intermediate/csr/intermediate.csr.pem -out intermediate/certs/intermediate.cert.pem
```
<br>

Команда openssl предполагает установку парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

```bash
chmod 444 intermediate/certs/intermediate.cert.pem
```
<br>

#### Проверка сертификата для INTERMEDIATE CA

```bash
openssl x509 -noout -text -in intermediate/certs/intermediate.cert.pem
```
<br>

```bash
openssl verify -CAfile certs/ca.cert.pem intermediate/certs/intermediate.cert.pem
```
<br>

#### Создание цепочки корневых сертификатов

```bash
cat intermediate/certs/intermediate.cert.pem certs/ca.cert.pem > intermediate/certs/ca-chain.cert.pem
```
<br>

```bash
chmod 444 intermediate/certs/ca-chain.cert.pem
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
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext
prompt = no
[ req_distinguished_name ]
countryName = RU
stateOrProvinceName = Moscow
localityName = Moscow
organizationName = SEA_TEST_ORG
commonName = *.sea.local
[ req_ext ]
subjectAltName = @alt_names
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
openssl genrsa -out intermediate/private/sea.local.key.pem 2048
```
<br>

```bash
chmod 400 intermediate/private/sea.local.key.pem
```
<br>

#### Создание CSR(certificate signing request) для серверного сертификата

```bash
openssl req -config intermediate/sea.local.cnf -key intermediate/private/sea.local.key.pem -new -sha256 -out intermediate/csr/sea.local.csr.pem
```
<br>

#### Создание серверного сертификата

```bash
openssl ca -config intermediate/openssl.cnf \
-extensions server_cert -days 375 -notext -md sha256 \
-in intermediate/csr/sea.local.csr.pem \
-out intermediate/certs/sea.local.cert.pem
```
<br>

```bash
chmod 444 intermediate/certs/sea.local.cert.pem
```
<br>

 #### Проверка сертификата

```bash
openssl x509 -noout -text -in intermediate/certs/sea.local.cert.pem
```
<br>

```bash
openssl verify -CAfile intermediate/certs/ca-chain.cert.pem \
intermediate/certs/sea.local.cert.pem
```
<br>



