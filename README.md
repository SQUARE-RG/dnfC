# dnfC

## 如何在docker内进行测试：
### 构建docker:
```
docker run --name dnfc -v <项目位置>:/code -it centos:8.4.2105 /bin/bash
docker run --name dnfc -v <项目位置>:/code -it openeuler/openeuler /bin/bash
```
进入docker后，在docker内执行:
```
sed -i -e "s|mirrorlist=|#mirrorlist=|g" /etc/yum.repos.d/CentOS-*
sed -i -e "s|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g" /etc/yum.repos.d/CentOS-*
yum clean all
yum makecache
(centos)
/usr/bin/yum -y install make curl-devel gcc python3-devel openssl-devel python3-numpy python3-pycurl python3-pyyaml python3-semantic_version python3-chardet python3-jsonschema python3-lxml python3-pyparsing python3-attrs python3-jsonpointer python3-idna python3-six python3-dateutil 
(openEuler)
/usr/bin/yum -y install make curl-devel gcc python3-devel openssl-devel python3-numpy python3-pyyaml python3-semantic_version python3-chardet python3-jsonschema python3-lxml python3-pyparsing python3-attrs python3-jsonpointer python3-idna python3-six python3-dateutil   python3-packaging  python3-referencing

python3-pycurl python3-certifi python3-requests python3-pyrpm python3-numpy



cd /code
#make build
echo "alias dnf='dnfc'" >> /etc/bashrc
echo "alias yum='dnfc'" >> /etc/bashrc
make install
```
### 运行docker:
```
docker start dnfc
docker exec -it dnfc /bin/bash
```
### 手动测试：
apt install xxx，此时会执行检查

### 自动测试：

测试集为`test/openEulerinfo.txt`，是openEuler 24.03版本对应的软件包，应在openEuler 24.03版本中测试

进入`/code/test`文件夹

```

mkdir binary #保存软件包分析结果
mkdir source #临时保存下载的源码包
mkdir src #保存源码包分析结果

```

使用`autotest_binary.py`自动下载测试集中的每个软件包并进行分析

使用`autotest_src.py`自动下载测试集中的每个项目的源码包并进行分析（一个源码包可能对应多个软件包）

此操作需要向服务端提交请求，请运行服务端，并在客户端编辑etc/aptC/config.json，配置服务端ip

使用`check.py`可以粗略对比通过二进制和通过源码生成的分析结果中，外部依赖是否不同

测试的原理是通过不同的方式分析依赖关系，将apt输出结果和内置分析模块的结果对比，确定内部分析模块的正确性

若要详细确认具体的软件包依赖信息，可以修改项目中src/SpecificPackage.py中debugMode，将其设为True。分别将`testbin.py`和`testsrc.py`中的`testName`修改为要测试的项目名，分别运行，会输出每个软件包依赖信息。

将`testbin.py`的输出结果重定向到`resbin.txt`，`testsrc.py`的输出结果重定向到`restsrc.txt`，可以运行`checkdiff.py`，自动对比两个文件差异

## 构建
### 在本地环境构建软件包
```
sudo dnf install rpmdevtools
sudo dnf install python3-pycurl python3-certifi python3-requests python3-pyrpm python3-numpy
sudo pip3 install pyinstaller
rpmdev-setuptree
cd ..
rm dnfC-1.0 -rf
cp dnfC dnfC-1.0 -r
tar czvf ~/rpmbuild/SOURCES/dnfC-1.0.tar.gz dnfC-1.0
cp dnfC-1.0/SPECS/dnfC.spec ~/rpmbuild/SPECS
cd ~/rpmbuild
rpmbuild -ba SPECS/dnfC.spec
```
`~/rpmbuild/RPMS/`文件夹下即为生成的rpm包

### 利用docker构建软件包

构建rpm软件包
```
docker build --output=<软件包保存目录> --build-arg SYSTEM_NAME="<操作系统名称(docker hub记录的名称)>" --build-arg VERSION="<发行版版本>" --target=rpm_package -f docker/dockerfile .
```
例如
```
docker build --output=. --build-arg SYSTEM_NAME="centos" --build-arg VERSION="8" --target=rpm_package -f docker/dockerfile .
```
或者
```
docker build --output=. --build-arg SYSTEM_NAME="openeuler/openeuler" --build-arg VERSION="24.03" --target=rpm_package -f docker/dockerfile .
```
