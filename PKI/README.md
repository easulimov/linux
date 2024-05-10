# Описывается пример создание своего центра сертификации
### Подготовка директорий
```bash
mkdir /root/ca
cd /root/ca
mkdir certs crl newcerts private
chmod 700 private
touch index.txt
echo 1000 > serial
```
<br>

### ROOT CA
#### Создание когнфигурационного файла для ROOT CA
Требуется создать файл с конфигурацией 
```bash
vim /root/ca/openssl.cnf
```
<br>
Содержимое файла ***/root/ca/openssl.cnf***

```ini
[ ca ]
#man ca
default_ca = CA_default

[ CA_default ]
# Directory and file locations.
dir               = /root/ca
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

# The root key and root certificate.  
 private_key       = $dir/private/ca.key.pem  
 certificate       = $dir/certs/ca.cert.pem

# For certificate revocation lists.  
 crlnumber         = $dir/crlnumber  
 crl               = $dir/crl/ca.crl.pem  
 crl_extensions    = crl_ext  
 default_crl_days  = 30

# SHA-1 is deprecated, so use SHA-2 instead.  
 default_md        = sha256

name_opt          = ca_default  
 cert_opt          = ca_default  
 default_days      = 375  
 preserve          = no  
 policy            = policy_strict


[ policy_strict ]
# The root CA should only sign intermediate certificates that match.
# See the POLICY FORMAT section of man ca.
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
# See https://en.wikipedia.org/wiki/Certificate_signing_request.
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name
localityName                    = Locality Name
organizationName                = Organization Name
organizationalUnitName          = Organizational Unit Name
commonName                      = Common Name
emailAddress                    = Email Address

# Optionally, specify some defaults.  
countryName_default             = RU  
stateOrProvinceName_default     = Moscow  
localityName_default            = Moscow  
organizationName_default       = SEA_TEST_ORG  
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

#### Создание private key для ROOT CA

```bash
cd /root/ca
openssl genrsa -aes256 -out private/ca.key.pem 4096
chmod 400 private/ca.key.pem
```
<br>

Команда openssl предполагает установки парольной фразы на ключ:
```
Enter pass phrase for ca.key.pem: secretpassword
Verifying - Enter pass phrase for ca.key.pem: secretpassword
```
<br>

#### Создание сертификата для ROOT CA

```bash
cd /root/ca
openssl req -config openssl.cnf -key private/ca.key.pem -new -x509 -days 7300 -sha256 -extensions v3_ca -out certs/ca.cert.pem
chmod 444 certs/ca.cert.pem
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
openssl req -config openssl.cnf -key private/ca.key.pem -new -x509 -days 7300 -sha256 -extensions v3_ca -out certs/ca.cert.pem
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
#### Проверка ROOT CA
```bash
openssl x509 -noout -text -in certs/ca.cert.pem
```

 



