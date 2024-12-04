%global _python_bytecompile_errors_terminate_build 0
%global debug_package %{nil}

Name: dnfC
Version: 1.0
Release: 1%{?dist}
Summary: Check package before install 
License:        GPL v2.0
Source0:        %{name}-%{version}.tar.gz

Requires:  python3

#BuildRequires:  python3 
#BuildRequires:  python3-pyinstaller 
#BuildRequires:  python3-pycurl python3-certifi python3-requests python3-pyrpm python3-numpy
#BuildRequires:  python3-semantic_version python3-chardet python3-jsonschema python3-lxml python3-pyparsing
#BuildRequires:  python3-attrs python3-jsonpointer python3-idna python3-six python3-dateutil python3-certifi
#BuildRequires:  python3-pyrpm python3-packaging python3-requests python3-referencing

%description
Check package before install 

%prep
rm -rf %{buildroot}
%setup -q

%build
#pip3 install wget loguru rarfile cyclonedx-bom cyclonedx-python-lib winrar pyzstd
#pyinstaller -F src/dnfc

%install

mkdir -p %{buildroot}/usr/sbin
cp %{_builddir}/%{name}-%{version}/dist/dnfc %{buildroot}/usr/sbin/dnf
mkdir -p %{buildroot}/usr/share/dnfC/spdx/
cp -r %{_builddir}/%{name}-%{version}/src/spdx/syft11 %{buildroot}/usr/share/dnfC/spdx/
cp -r %{_builddir}/%{name}-%{version}/src/spdx/syft %{buildroot}/usr/share/dnfC/spdx/
mkdir -p %{buildroot}/usr/share/dnfC/license_expression/
cp -r %{_builddir}/%{name}-%{version}/src/license_expression/data %{buildroot}/usr/share/dnfC/license_expression/
mkdir -p %{buildroot}/usr/share/dnfC/cyclonedx/
cp -r %{_builddir}/%{name}-%{version}/src/cyclonedx %{buildroot}/usr/share/dnfC/
mkdir -p %{buildroot}/etc/
cp -r %{_builddir}/%{name}-%{version}/etc/dnfC %{buildroot}/etc/

%files
%defattr(-,root,root,-)
/usr/share/dnfC/*
/usr/sbin/*
/etc/dnfC/*
%post

#ln -s /usr/sbin/dnfc /usr/sbin/dnf
#ln -s /usr/sbin/dnfc /usr/sbin/yum

#sed -i "/set PATH='\/share\/dnfC\/bin;\$PATH'/d" /etc/bashrc
#echo "set PATH='/share/dnfC/bin;\$PATH'" >> /etc/bashrc
%preun


%postun

#rm -f /usr/sbin/dnf
#rm -f /usr/sbin/yum
#sed -i "/set PATH='/share/dnfC/bin;\$PATH'/d" /etc/bashrc

%changelog



