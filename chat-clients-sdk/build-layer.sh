#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
CWD=$(pwd)

## preflight checks
if [ -d .venv/bin ]; then
    . .venv/bin/activate
else
    echo "WARNING: .venv/bin not found. Please install the python virtual environment."
    echo "         Follow the project documentation for more information."
    echo "         Also check the Prerequisites documentation."
fi

if [ -z "$VIRTUAL_ENV" ]; then
    project_name=$(basename $CWD)
    echo "You are not running in a .venv environment. Click the + icon on the top-right to launch a .venv in '${project_name}'!"
    exit 1
fi

python -V

# OS="`uname`"
# if [ "$OS" != "Linux" ]; then
#     echo "Error: You must build lambda layer in Linux environment"
#     echo "Current OS: $OS"
#     exit 1
# fi

if [ ! -d "build" ]; then
    echo "creating build folder"
    mkdir -p build
fi

## generate python 3.12+ stdlib modules in a temporary file /tmp/$$.p3.stdlib.modules.txt
## refer to https://docs.python.org/3/library/index.html for the list of stdlib modules
generate_stdlib_modules() {
    echo "generating python 3.12+ stdlib modules"
    cat > /tmp/$$.p3.stdlib.modules.txt << EOF
string
re
difflib
textwrap
unicodedata
stringprep
readline
rlcompleter
struct
codecs
datetime
zoneinfo
calendar
collections
heapq
bisect
array
weakref
types
copy
pprint
reprlib
enum
graphlib
numbers
math
cmath
decimal
fractions
random
statistics
itertools
functools
operator
pathlib
os
fileinput
stat
filecmp
tempfile
glob
fnmatch
linecache
shutil
pickle
copyreg
shelve
marshal
dbm
sqlite3
zlib
gzip
bz2
lzma
zipfile
tarfile
csv
configparser
tomllib
netrc
plistlib
hashlib
hmac
secrets
os
io
time
argparse
getopt
logging
getpass
curses
platform
errno
ctypes
threading
multiprocessing
concurrent
subprocess
sched
queue
contextvars
_thread
asyncio
socket
ssl
select
selectors
signal
mmap
email
json
mailbox
mimetypes
base64
binascii
quopri
html
xml
webbrowser
wsgiref
urllib
http
ftplib
poplib
imaplib
smtplib
uuid
socketserver
xmlrpc
ipaddress
wave
colorsys
gettext
locale
turtle
cmd
shlex
tkinter
typing
pydoc
doctest
unittest
2to3
test
bdb
faulthandler
pdb
timeit
trace
tracemalloc
ensurepip
venv
zipapp
sys
sysconfig
builtins
warnings
dataclasses
contextlib
abc
atexit
traceback
__future__
gc
inspect
site
code
codeop
zipimport
pkgutil
modulefinder
runpy
importlib
ast
symtable
token
keyword
tokenize
tabnanny
pyclbr
py_compile
compileall
dis
pickletools
msvcrt
winreg
winsound
posix
pwd
grp
termios
tty
pty
fcntl
resource
syslog
aifc
audioop
cgi
cgitb
chunk
crypt
imghdr
mailcap
msilib
nis
nntplib
optparse
ossaudiodev
pipes
sndhdr
spwd
sunau
telnetlib
uu
xdrlib
EOF
}

## create method to clean requirements.txt of all unnecessary python libraries that are provided by Lambda python runtime
clean_requirements() {
    requirements_file=$1
    echo "cleaning requirements.txt"

    # iterate over /tmp/$$.p3.stdlib.modules.txt and remove modules from requirements.txt
    cat /tmp/$$.p3.stdlib.modules.txt | while read module; do
        cat $requirements_file | sed -e "/^$module[\.\S]*\s*[><=!]*.*/d" > /tmp/$$.cleansed.requirements.txt
        mv /tmp/$$.cleansed.requirements.txt $requirements_file
        chmod 644 $requirements_file
        echo $module
    done

    # add additional module names to clean from requirements into a temp file
    cat > /tmp/$$.additional.modules.txt << EOF
boto3
botocore
EOF

    # iterate over /tmp/$$.additional.modules.txt and remove modules from requirements.txt
    cat /tmp/$$.additional.modules.txt | while read module; do
        cat $requirements_file | sed -e "/^$module[\.\S]*\s*[><=!]*.*/d" > /tmp/$$.cleansed.requirements.txt
        mv /tmp/$$.cleansed.requirements.txt $requirements_file
        chmod 644 $requirements_file
        echo $module
    done
}

## more preflight checks
layer_version=$(grep '^version' pyproject.toml | sed -e 's/.*"\(.*\)"[\n\r]*/\1/g')
layer_short_name="chat-clients"
layer_wheel_name=$(echo "${layer_short_name}" | sed -e 's/-/_/g')
layer_name="${layer_short_name}-sdk-layer-${layer_version}"

echo
echo "Working directory: ${CWD}"
echo "Layer name: ${layer_name}"
echo

# check if layer whl library exists in root dist folder
if [ ! -f "dist/${layer_wheel_name}-${layer_version}-py3-none-any.whl" ]; then
    echo "${layer_wheel_name}-${layer_version}-py3-none-any.whl library not found in root dist folder"
    echo "forgot to build the library?"
    exit 1
fi

## initialize build folder
echo "preparing"
(
    cd build
    if [ $? -ne 0 ]; then
        echo "failed during prepare step"
        rm -rf /tmp/$$.*
        exit 3
    fi

    rm -rf compressed python && mkdir compressed && mkdir python
) > /tmp/$$.build-layer.prepare.log 2>&1
if [ $? -ne 0 ]; then
    echo "failed during prepare step"
    cat /tmp/$$.build-layer.prepare.log
    rm -rf /tmp/$$.*
    exit 2
fi

## create requirements.txt file
echo "generating requirements.txt"

# generate build/requirements.txt file
(
    # generate python 3.12+ stdlib modules
    generate_stdlib_modules

    # make a copy of requirements.txt
    cp requirements.txt build/requirements.txt

    # clean build/requirements.txt by removing python stdlib module names and boto3/botocore modules
    clean_requirements build/requirements.txt

    # add sdk layer_wheel_name to requirements.txt
    # echo "../../dist/${layer_wheel_name}-${layer_version}-py3-none-any.whl" >> build/requirements.txt

) >/tmp/$$.build-layer.requirements.log 2>&1
if [ $? -ne 0 ]; then
    echo "failed during requirements.txt generation step"
    cat /tmp/$$.build-layer.requirements.log
    rm -rf /tmp/$$.*
    exit 2
fi

## build layer

# IMPORTANT: another way to package libraries is using binary only mode documened below
#   https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-native-libraries
# however this method doesn't work with langchain and pydantic dependancies

# Check
# https://stackoverflow.com/questions/67646196/aws-lambda-python-cryptography-cannot-open-shared-object-files
# https://medium.com/@jackyw2017/how-to-create-a-lambda-layer-for-python-dependencies-on-macos-e2aeea80a272

echo "building layer"
(
    # cd build/python && pip install --no-cache-dir --target=. --requirement ../requirements.txt
    # cp dist/*.whl build/python

    cd build/python

    pip3 install --platform manylinux2014_x86_64 --implementation cp --no-deps --no-cache-dir --target=. ../../dist/${layer_wheel_name}-${layer_version}-py3-none-any.whl --upgrade
    pip3 install --platform manylinux2014_x86_64 --implementation cp --no-cache-dir --target=. -r ../requirements.txt --only-binary=:all: --upgrade

    # remove boto3 , botocore from virtual environment
    rm -rf boto3* botocore*
    # remove all python 3.12 stdlib packages from virtual environment if they were installed - https://docs.python.org/3/library/index.html
    cat /tmp/$$.p3.stdlib.modules.txt | while read module; do
        rm -rf "${module}"
        rm -rf "${module}-*"
    done
) >/tmp/$$.build-layer.build.log 2>&1


if [ $? -ne 0 ]; then
    echo "failed during build step"
    cat /tmp/$$.build-layer.build.log
    rm -rf /tmp/$$.*
    exit 2
fi

# remove redundant stuff
echo "trimming up layer"
(
    cd build/python
    if [ $? -ne 0 ]; then
        echo "failed during trim step"
        rm -rf /tmp/$$.*
        exit 3
    fi
    find ./ -type d -name "__pycache__" -exec rm -rf {} +
    find ./ -type f -name "*.pyc" -delete
    find ./ -name '*.so*' -type f -exec strip "{}" \;
    # find ./ -type d -name "docs" -exec rm -rf {} +
    # find ./ -type d -name "tests" -exec rm -rf {} +
    # rm -rf *.dist-info
) >/tmp/$$.build-layer.clean.log 2>&1
if [ $? -ne 0 ]; then
    echo "failed during clean step"
    cat /tmp/$$.build-layer.clean.log
    rm -rf /tmp/$$.*
    exit 2
fi

# add resources/ca-certs.crt to build/python/certi/cacerts.pem
# ensure that ca-certs.crt is non-zero and contains valid list of
# pem certificates using openssl
project_ca_certs="resources/ca-certs.crt"
if [ -d "`dirname ${project_ca_certs}`" -a -s "${project_ca_certs}" ]; then
    (
        echo "adding ca-certs.crt to build/python/certi/cacerts.pem"
        # verify ca-certs.crt is valid pem certificate using openssl
        while openssl x509 -noout -text; do :; done < "${project_ca_certs}" >>/tmp/$$.ca-cert.verify.log 2>&1
        if [ $? -ne 0 ]; then
            echo "invalid ca-certs.crt"
            cat /tmp/$$.ca-cert.verify.log
            rm -rf /tmp/$$.*
            exit 3
        fi

        python_ca_certs="build/python/certi/cacerts.pem"
        if [ ! -f "${python_ca_certs}"]; then
            echo "missing certi/cacerts.pem"
            rm -rf /tmp/$$.*
            exit 3
        fi

        # append ca-certs.crt to cacerts.pem
        cat "${project_ca_certs}" >> "${python_ca_certs}"
        chmod 644 cacerts.pem

        # do one final verification on python_ca_certs to ensure it's valid
        while openssl x509 -noout -text; do :; done < "${python_ca_certs}" >>/tmp/$$.certi-cacerts.verify.log 2>&1
        if [ $? -ne 0 ]; then
            echo "invalid build/python/certi/cacerts.pem"
            cat /tmp/$$.certi-cacerts.verify.log
            rm -rf /tmp/$$.*
            exit 3
        fi
    ) >/tmp/$$.build-layer.certificate 2>&1
    if [ $? -ne 0 ]; then
        echo "failed while adding resources/ca-certs.crt"
        cat /tmp/$$.build-layer.certificate
        rm -rf /tmp/$$.*
        exit 3
    fi
fi

## create layer
echo "creating distribution zip"
(
    cd build && zip -r "compressed/${layer_name}.zip" python
) >/tmp/$$.build-layer.zip 2>&1
if [ $? -ne 0 ]; then
    echo "failed during zip step"
    cat /tmp/$$.build-layer.zip
    rm -rf /tmp/$$.*
    exit 2
fi

## clean up
rm -rf /tmp/$$.*
echo "done!"
