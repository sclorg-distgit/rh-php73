%{!?scl_vendor: %global scl_vendor rh}
%global scl_name_base    php
%global scl_name_version 73
%global scl              %{scl_vendor}-%{scl_name_base}%{scl_name_version}
%global macrosdir        %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_root_sysconfdir}/rpm; echo $d)
%global install_scl      1
%global nfsmountable     1

%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary:       Package that installs PHP 7.3
Name:          %scl_name
Version:       1
Release:       1%{?dist}
Group:         Development/Languages
License:       GPLv2+

Source0:       macros-build
Source1:       README
Source2:       LICENSE
Source3:       register
Source4:       deregister
Source5:       50-copy-files
Source6:       50-clean-files

BuildRequires: scl-utils-build
BuildRequires: help2man
# Temporary work-around
BuildRequires: iso-codes

Requires:      %{?scl_prefix}php-common%{?_isa}
Requires:      %{?scl_prefix}php-cli%{?_isa}
Requires:      %{?scl_prefix}php-pear
Requires:      %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description
This is the main package for %scl Software Collection,
that install PHP 7.3 language.


%package runtime
Summary:   Package that handles %scl Software Collection.
Group:     Development/Languages
Requires:  scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.


%package build
Summary:   Package shipping basic build configuration
Group:     Development/Languages
Requires:  scl-utils-build
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description build
Package shipping essential configuration macros
to build %scl Software Collection.


%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.


%prep
%setup -c -T

cat <<EOF | tee enable
export PATH=%{_bindir}:%{_sbindir}\${PATH:+:\${PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE1})}
EOF

# copy additional files
cp %{SOURCE2} %{SOURCE3} %{SOURCE4} %{SOURCE5} %{SOURCE6} .


%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7
# Fix single quotes in man page. See RHBZ#1219527
#
# http://lists.gnu.org/archive/html/groff/2008-06/msg00001.html suggests that
# using "'" for quotes is correct, but the current implementation of man in 6
# mangles it when rendering.
sed -i "s/'/\\\\(aq/g" %{scl_name}.7
 

%install
install -D -m 644 enable         %{buildroot}%{_scl_scripts}/enable
install -D -m 644 register       %{buildroot}%{_scl_scripts}/register
install -d -m 755                %{buildroot}%{_scl_scripts}/register.content
install -D -m 644 50-copy-files  %{buildroot}%{_scl_scripts}/register.d/50-copy-files
install -D -m 644 deregister     %{buildroot}%{_scl_scripts}/deregister
install -D -m 644 50-clean-files %{buildroot}%{_scl_scripts}/deregister.d/50-clean-files
sed -e 's:@SCLDIR@:%{_scl_scripts}:' \
    -i %{buildroot}%{_scl_scripts}/*gister

install -D -m 644 scldev %{buildroot}%{macrosdir}/macros.%{scl_name_base}-scldevel
install -D -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

install -d -m 755 %{buildroot}%{_datadir}/licenses
install -d -m 755 %{buildroot}%{_datadir}/doc/pecl
install -d -m 755 %{buildroot}%{_datadir}/tests/pecl
install -d -m 755 %{buildroot}%{_scl_root}/var/lib/pear/pkgxml
# Woraround scl-utils bug #1487085
%ifarch ppc64le aarch64
install -d -m 755 %{buildroot}%{_scl_root}/usr/lib64
ln -s  usr/lib64  %{buildroot}%{_scl_root}/lib64
%endif

%scl_install

# Add the scl_package_override macro
sed -e 's/@SCL@/%{scl_name_base}%{scl_name_version}/g' \
    -e 's/@VENDOR@/%{scl_vendor}/' \
    %{SOURCE0} \
  | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config

# Move in correct location, if needed
if [ "%{_root_sysconfdir}/rpm" != "%{macrosdir}" ]; then
  mv  %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config \
      %{buildroot}%{macrosdir}/macros.%{scl}-config
fi


%post runtime
# Simple copy of context from system root to SCL root.
semanage fcontext -a -e /                      %{?_scl_root}     &>/dev/null || :
semanage fcontext -a -e %{_root_sysconfdir}    %{_sysconfdir}    &>/dev/null || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} &>/dev/null || :
selinuxenabled && load_policy || :
restorecon -R %{?_scl_root}     &>/dev/null || :
restorecon -R %{_sysconfdir}    &>/dev/null || :
restorecon -R %{_localstatedir} &>/dev/null || :


%files


%{!?_licensedir:%global license %%doc}

%if 0%{?fedora} < 19 && 0%{?rhel} < 7
%files runtime
%else
%files runtime -f filesystem
%endif
%license LICENSE
%doc README
%scl_files
%{_scl_scripts}/register
%{_scl_scripts}/register.d/
%{_scl_scripts}/register.content/
%{_scl_scripts}/deregister
%{_scl_scripts}/deregister.d/
%{?_licensedir:%{_datadir}/licenses}
%{_datadir}/tests
%{_scl_root}/var
%ifarch ppc64le aarch64
%{_scl_root}/lib64
%{_scl_root}/usr/lib64
%endif


%files build
%{macrosdir}/macros.%{scl}-config


%files scldevel
%{macrosdir}/macros.%{scl_name_base}-scldevel


%changelog
* Fri Jul 12 2019 Remi Collet <rcollet@redhat.com> 1-1
- initial package for rh-php73 in RHSCL-3.4

* Mon Jul 16 2018 Remi Collet <rcollet@redhat.com> 1-2
- fix /usr/lib64 ownership on ppc64le and aarch64

* Tue Jul 10 2018 Remi Collet <rcollet@redhat.com> 1-1
- initial package for rh-php72 in RHSCL-3.2

* Thu Jun  1 2017 Remi Collet <rcollet@redhat.com> 1-1
- initial package for rh-php71 in RHSCL-3.0

* Thu Jul 21 2016 Remi Collet <rcollet@redhat.com> 2.3-1
- initial package for rh-php70 in RHSCL-2.3

* Mon Mar 16 2015 Remi Collet <rcollet@redhat.com> 2.0-6
- rebuild to remove scls directory #1200056
- fix incorrect selinux contexts #1194337

* Wed Jan 28 2015 Remi Collet <rcollet@redhat.com> 2.0-5
- own licenses and tests directory

* Mon Jan 26 2015 Remi Collet <rcollet@redhat.com> 2.0-4
- silent rmdir in deregister script

* Mon Jan 26 2015 Remi Collet <rcollet@redhat.com> 2.0-3
- add register and deregister scripts

* Wed Jan 14 2015 Remi Collet <rcollet@redhat.com> 2.0-2
- drop scl_vendor prefix from macro

* Tue Jan 13 2015 Remi Collet <rcollet@redhat.com> 2.0-1
- initial package for rh-php56 in RHSCL-2.0

* Wed Nov 26 2014 Remi Collet <remi@fedoraproject.org> 2.0-2
- add LD_LIBRARY_PATH in enable script for embedded

* Mon Sep  8 2014 Remi Collet <remi@fedoraproject.org> 2.0-1
- provides php56-runtime(remi)
- add _sclreq macro

* Sun Aug 24 2014 Remi Collet <rcollet@redhat.com> 1.0-1
- initial packaging from php55 from rhscl 1.1
- install macro in /usr/lib/rpm/macros.d
- each package requires runtime (for license)

* Mon Mar 31 2014 Honza Horak <hhorak@redhat.com> - 1.1-7
- Fix path typo in README
  Related: #1061455

* Mon Mar 24 2014 Remi Collet <rcollet@redhat.com> 1.1-6
- own locale and man directories, #1074337

* Wed Feb 12 2014 Remi Collet <rcollet@redhat.com> 1.1-5
- avoid empty debuginfo subpackage
- add LICENSE, README and php55.7 man page #1061455
- add scldevel subpackage #1063357

* Mon Jan 20 2014 Remi Collet <rcollet@redhat.com> 1.1-4
- rebuild with latest scl-utils #1054731

* Tue Nov 19 2013 Remi Collet <rcollet@redhat.com> 1.1-2
- fix scl_package_override

* Tue Nov 19 2013 Remi Collet <rcollet@redhat.com> 1.1-1
- build for RHSCL 1.1

* Tue Sep 17 2013 Remi Collet <rcollet@redhat.com> 1-1.5
- add macros.php55-build for scl_package_override

* Fri Aug  2 2013 Remi Collet <rcollet@redhat.com> 1-1
- initial packaging
