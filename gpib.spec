# Conditional build with a command line option - (the default condition is the opposite)
%bcond_without guile
%bcond_without docs
%bcond_without perl
%bcond_without php
%bcond_without python3
%bcond_without tcl

# https://sourceforge.net/p/linux-gpib/git/ci/eeb0307df9e2b53b17e488bac720e5139040b453/tree/
%global gitrev e6e13a0f349a3298ee2f689da969efd6e39f96c3
%global gitdate 20260121

%global _hardened_build 1

%{?with_guile:%global guile_site %{_datadir}/guile/site}

%{?with_perl:%global perlname LinuxGpib}

%if %{with tcl}
    # this is hacky, since the copr buildroot doesn't currently provide tclsh
    # adapted from <https://src.fedoraproject.org/rpms/tcl-togl/blob/master/f/tcl-togl.spec> 
    %global tcl_version_default \
        %((rpm -q --qf '%%{VERSION}\\n' tcl-devel | tail -1 | cut -c 1-3))
    %{!?tcl_version: %global tcl_version %((echo '%{tcl_version_default}'; echo 'puts $tcl_version' | tclsh 2>/dev/null) | tail -1)}
    %{!?tcl_sitearch: %global tcl_sitearch %{_libdir}/tcl%{tcl_version}}
%endif

Name:           gpib
Version:        4.3.7
Release:        3%{?dist}
Summary:        Linux GPIB (IEEE-488) userspace library and programs

License:        GPL-2.0-or-later
URL:            http://linux-gpib.sourceforge.net/

Obsoletes: linux-%{name} <= %{version}
%global upstream_name linux-%{name}

# The source for this package was pulled from upstream's vcs. Use the
# below commands to generate the zip or use the SourceForge website.
# We use zip instead of tar.gz since that is what is on SourceForge
#  $ wget https://sourceforge.net/code-snapshots/git/l/li/linux-gpib/git.git/linux-gpib-git-44e3d07dfc6836929d81e808a269e3143054b233.zip
#  $ git clone https://git.code.sf.net/p/linux-gpib/git linux-gpib-git

Source0:        %{upstream_name}-git-%{gitrev}.zip
Source1:        60-%{name}-adapter.rules
Source2:        %{name}-config@.service.in
Source3:        %{name}-config-systemd

# We package our own udev rules and firmware loader
Patch0:         %{name}-remove-usb-autotools.patch

Requires(post):   /sbin/ldconfig
Requires(postun): /sbin/ldconfig

BuildRequires:  autoconf >= 2.50
BuildRequires:  automake
BuildRequires:  libtool

BuildRequires:  sed

BuildRequires:  gcc
BuildRequires:  flex
BuildRequires:  bison

BuildRequires:  libxslt
BuildRequires:  python3-setuptools
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-pip
BuildRequires:  perl
BuildRequires:  docbook5-style-xsl
BuildRequires:  dblatex
BuildRequires:  opensp
BuildRequires:  texlive-jadetex
BuildRequires:  texlive-dvips
BuildRequires:  texlive-metafont
BuildRequires:  texlive-wasy
BuildRequires:  docbook5-schemas

%{?systemd_requires}
BuildRequires:  systemd


%description
The Linux GPIB package provides support for GPIB (IEEE-488) hardware.
This packages contains the userspace libraries and programs.


%package devel
Summary:        Development files for %{name}

Requires:       %{name}%{?_isa} = %{version}-%{release}

Obsoletes: linux-%{name}-devel <= %{version}

%description devel
Development files for %{name}.

%if %{with guile}
%package -n guile18-%{name}
Summary:        Guile %{name} module

Requires:       compat-guile18%{?_isa}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  compat-guile18-devel

Obsoletes: guile18-linux-%{name} <= %{version}

%description -n guile18-%{name}
Guile bindings for %{name}.
%endif


%if %{with php}
%package -n php-%{name}
Summary:        PHP %{name} module

Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
BuildRequires:  php-devel

Obsoletes: php-linux-%{name} <= %{version}

%description -n php-%{name}
PHP bindings for %{name}.
%endif


%if %{with perl}
%package -n perl-%{perlname}
Summary:        Perl %{name} module

Requires:       perl
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  perl-devel
BuildRequires:  perl(ExtUtils::MakeMaker)
BuildRequires:  perl(Test)

%description -n perl-%{perlname}
Perl bindings for %{name}.
%endif

%if %{with python3}
%package -n python%{python3_pkgversion}-%{name}
Summary:        Python 3 %{name} module

%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  python%{python3_pkgversion}-devel

Obsoletes: python%{python3_pkgversion}-linux-%{name} <= %{version}

%description -n python%{python3_pkgversion}-%{name}
Python 3 bindings for %{name}.
%endif


%if %{with tcl}
%package -n tcl-%{name}
Summary:        TCL %{name} module

Requires:       tcl(abi) = %{tcl_version}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  tcl-devel

Obsoletes: tcl-linux-%{name} <= %{version}

%description -n tcl-%{name}
TCL bindings for %{name}.
%endif


%if %{with docs}
%package doc
Summary:        Documentation for %{name} library

BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}

Obsoletes: linux-%{name}-doc <= %{version}

%description doc
HTML and PDF documentation for %{name}.
%endif


%prep
%setup -q -n %{upstream_name}-git-%{gitrev}

%patch 0 -p1

%build
pushd %{upstream_name}-user
touch ChangeLog
autoreconf -vif

# we make the docs, and the Perl and Python bindings in the spec, 
# not the library's Makefile (see the docs section below)
%configure \
    %{!?with_guile:--disable-guile18-binding} \
    %{!?with_php:--disable-php-binding} \
    %{!?with_tcl:--disable-tcl-binding} \
    --disable-documentation \
    --disable-html-docs \
    --disable-manpages \
    --disable-python-binding \
    --disable-perl-binding \
    --disable-static \
    --sbindir=%{_sbindir} YACC=bison 

%make_build

pushd language
%if %{with perl}
    %{__make} perl/Makefile.PL

    pushd perl
    %{__perl} Makefile.PL INSTALLDIRS=vendor NO_PACKLIST=1 OPTIMIZE="%{optflags}"
    %make_build
    popd
%endif

pushd python
%{?with_python3:%pyproject_wheel}
popd
popd # language
popd # %%{name}-user


%install
# build directory tree
install -d %{buildroot}%{_docdir}/%{name}
install -d %{buildroot}%{_mandir}/{man1,man3,man5,man8,mann}

%{?with_guile:install -d %{buildroot}%{guile_site}}
%{?with_tcl:install -d %{buildroot}%{tcl_sitearch}/%{name}}

# userspace
pushd %{upstream_name}-user
%make_install

pushd language
pushd guile
%{?with_guile:install -p -m 0644 gpib.scm %{buildroot}%{guile_site}}
popd

pushd perl
%{?with_perl:%{__make} pure_install DESTDIR=%{buildroot}}
popd

pushd python
%{?with_python3:%pyproject_install}
popd

pushd tcl
%if %{with tcl}
    mv %{buildroot}%{_libdir}/*_tcl* %{buildroot}%{tcl_sitearch}/%{name}
    install -p -m 0644 gpib.n %{buildroot}%{_mandir}/mann
%endif
popd
popd # language

pushd doc
echo '<phrase xmlns="http://docbook.org/ns/docbook" version="5.0">%{version}</phrase>' > %{name}-version.xml
echo %{version} > gpib_version.txt;
osx -x no-expand-internal -x no-internal-decl -x preserve-case %{upstream_name}.sgml > %{name}.xml
     xsltproc --param man.authors.section.enabled 0 \
              --param man.output.in.separate.dir 1 \
              %{_datadir}/sgml/docbook/xsl-ns-stylesheets/manpages/docbook.xsl \
              %{name}.xml
for mandir in man1 man3 man5 man8 ; do
    install -p -m 0644 man/$mandir/* %{buildroot}%{_mandir}/$mandir
done

%if %{with docs}
    dblatex %{upstream_name}.sgml -F sgml -P table.in.float=none -o %{name}.pdf
        xsltproc --param generate.revhistory.link 1 \
             --param generate.section.toc.level 2 \
             --param make.clean.html 1 \
             --param table.borders.with.css 1 \
             --param use.id.as.filename 1 \
             --stringparam base.dir "doc_html" \
             --stringparam chunker.output.omit-xml-declaration "yes" \
             --stringparam html.ext ".html" \
             --xinclude \
             %{_datadir}/sgml/docbook/xsl-ns-stylesheets/xhtml5/chunk.xsl \
             %{name}.xml
    install -p -m 0644 %{name}.pdf %{buildroot}%{_docdir}/%{name}

    install -p -m 0644 %{name}-version.xml %{buildroot}%{_docdir}/%{name}
    install -p -m 0644 %{name}.xml %{buildroot}%{_docdir}/%{name}
    install -p -m 0644 obsolete-linux-gpib.txt %{buildroot}%{_docdir}/%{name}

    install -d %{buildroot}%{_docdir}/%{name}/html
    install -p -m 0644 doc_html/* %{buildroot}%{_docdir}/%{name}/html
%endif
popd # doc

# udev rules
install -d %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}

# systemd config unit
install -d %{buildroot}%{_unitdir}
sed -e 's|@libexecdir@|%{_libexecdir}|g' %{SOURCE2} > %{name}-config@.service
install -p -m 0644 %{name}-config@.service %{buildroot}%{_unitdir}

# systemd config script
install -d %{buildroot}%{_libexecdir}
install -p -m 0755 %{SOURCE3} %{buildroot}%{_libexecdir}
popd # %%{name}-user

# Cleanup
# remove libtool stuff
find %{buildroot} -name '*.la' -delete

# remove .gitignore
find %{buildroot} -name '.gitignore' -delete

# ... and automake caches `make dist` didn't get rid of
find %{buildroot} -name '.cache.mk' -delete

# ... and static libraries for language bindings
%{?with_guile:rm -f %{buildroot}%{_libdir}/*-guile.a}
%{?with_tcl:rm -f %{buildroot}%{tcl_sitearch}/%{name}/*_tcl.a}

# ... and .packlist for EPEL7 package
%{?with_perl:find %{buildroot} -type f -name '*.packlist' -delete}


%check
pushd %{upstream_name}-user/language/perl
%{?with_perl:%{__make} test LD_LIBRARY_PATH=%{buildroot}%{_libdir}}
popd

# Post-install stuff

# systemd stuff
%post
%systemd_post %{name}-config@.service
%{?ldconfig}

%preun
%systemd_preun %{name}-config@.service

%postun 
%systemd_postun %{name}-config@.service
%{?ldconfig}

# and ldconfig
%ldconfig_scriptlets devel

%{?with_guile:%ldconfig_scriptlets -n guile18-%{name}}

%{?with_tcl:%ldconfig_scriptlets -n tcl-%{name}}

%{?ldconfig}
udevadm control --reload > /dev/null 2>&1 || :

# 'remove' or 'purge' are the possible names for deb packages.
if [ "$1" = "0" -o "$1" = "remove" -o "$1" = "purge" ] ; then
    %{?ldconfig}
    udevadm control --reload > /dev/null 2>&1 || :
else
    echo "Script parameter $1 did not match any removal condition."
fi

%files
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/README

%attr(755,root,root) %{_bindir}/ibterm
%attr(755,root,root) %{_bindir}/findlisteners
%attr(755,root,root) %{_bindir}/ibtest
%attr(755,root,root) %{_sbindir}/gpib_config
%attr(755,root,root) %{_libexecdir}/gpib-config-systemd

%{_mandir}/man1/*
%{_mandir}/man3/*
%{_mandir}/man5/*
%{_mandir}/man8/*

%{_libdir}/libgpib.so.*

%config(noreplace) %{_sysconfdir}/gpib.conf

%{_unitdir}/*.service
%{_udevrulesdir}/*.rules

%files devel
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/README

%dir %{_includedir}/gpib

%{_includedir}/gpib/gpib_user.h
%{_includedir}/gpib/ib.h
%{_includedir}/gpib/gpib.h
%{_includedir}/gpib/gpib_version.h
%{_libdir}/pkgconfig/libgpib.pc
%{_libdir}/libgpib.so

%{_mandir}/man3/*.3*

%if %{with perl}
%exclude %{_mandir}/man3/*.3pm*
%endif


%if %{with guile}
%files -n guile18-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/guile/README

%{_libdir}/*-guile*.so
%{guile_site}/*.scm
%endif


%if %{with php}
%files -n php-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING

%{php_extdir}/*.so
%endif


%if %{with python3}
%files -n python%{python3_pkgversion}-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/python/README

%{python3_sitearch}/*
%endif


%if %{with perl}
%files -n perl-%{perlname}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/perl/README

%dir %{perl_vendorarch}/auto/%{perlname}

%{perl_vendorarch}/%{perlname}.pm
%{perl_vendorarch}/auto/%{perlname}/%{perlname}.*
%{perl_vendorarch}/auto/%{perlname}/autosplit.ix

%{_mandir}/man3/*.3pm*
%endif


%if %{with tcl}
%files -n tcl-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/tcl/README

%{tcl_sitearch}/%{name}

%{_mandir}/mann/gpib.n*
%endif


%if %{with docs}
%files doc
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING

%{_docdir}/%{name}
%endif


%changelog
* Wed Jan 21 2026 Michael Katzmann <vk2bea-at-gmail-dot-com>
- e6e13a0f349a3298ee2f689da969efd6e39f96c3 - INES PCI support
* Sun Jan 11 2026 Michael Katzmann <vk2bea-at-gmail-dot-com>
- Initial release

