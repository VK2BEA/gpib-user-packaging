# https://sourceforge.net/p/linux-gpib/git/ci/2b4cefbc91fd1523aff825fe6e958be112bc8645/tree/
%global gitrev 2b4cefbc91fd1523aff825fe6e958be112bc8645
%global gitdate 20260430

%global soversion 0

%global _hardened_build 1

%global guile_site %{_datadir}/guile/site

%global perlname LinuxGpib

Name:           gpib
Version:        4.3.7^%{gitdate}%(expr substr "%{gitrev}" 1 7)
Release:        %autorelease
Summary:        Linux GPIB (IEEE-488) userspace library and programs

License:        GPL-3.0-only
URL:            http://linux-gpib.sourceforge.net/

%global upstream_name linux-%{name}

Source0:        %{upstream_name}-git-2b4cefbc91fd1523aff825fe6e958be112bc8645.zip
Source1:        60-%{name}-adapter.rules
Source2:        %{name}-config@.service.in
Source3:        %{name}-config-systemd

# We package our own udev rules and firmware loader
Patch0:         %{name}-remove-usb-autotools.patch
Patch1:         %{name}-guile.patch

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
BuildRequires:  docbook-utils

%{?systemd_requires}
BuildRequires:  systemd

%description
The Linux GPIB package provides support for GPIB (IEEE-488) hardware.
This packages contains the userspace libraries and programs.


%package devel
Summary:        Development files for %{name}

Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Development files for %{name}.

%package -n guile18-%{name}
Summary:        Guile %{name} module

Requires:       compat-guile18%{?_isa}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  compat-guile18-devel

%description -n guile18-%{name}
Guile bindings for %{name}.


%package -n php-%{name}
Summary:        PHP %{name} module

Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  php-devel

%description -n php-%{name}
PHP bindings for %{name}.


%package -n perl-%{perlname}
Summary:        Perl %{name} module

Requires:       perl
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  perl(ExtUtils::MakeMaker)
BuildRequires:  perl(Test)

%description -n perl-%{perlname}
Perl bindings for %{name}.


%package -n python3-%{name}
Summary:        Python 3 %{name} module

%{?python_provide:%python_provide python3-%{name}}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  python3-devel

%description -n python3-%{name}
Python 3 bindings for %{name}.


%package -n tcl-%{name}
Summary:        TCL %{name} module

%global tcl_version_default \
        %((rpm -q --qf '%%{VERSION}\\n' tcl-devel | tail -1 | cut -c 1-3))
%{!?tcl_version: %global tcl_version %((echo '%{tcl_version_default}'; echo 'puts $tcl_version' | tclsh 2>/dev/null) | tail -1)}
%{!?tcl_sitearch: %global tcl_sitearch %{_libdir}/tcl%{tcl_version}}

Requires:       tcl(abi) = %{tcl_version}
Requires:       %{name}%{?_isa} = %{version}-%{release}
BuildRequires:  tcl-devel
BuildRequires:  tcl

%description -n tcl-%{name}
TCL bindings for %{name}.


%package doc
Summary:        Documentation for %{name} library

BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}

%description doc
HTML and PDF documentation for %{name}.

%prep
%setup -q -n %{upstream_name}-git-%{gitrev}
%autopatch -p1 -v

%build
pushd %{upstream_name}-user
  touch ChangeLog
  autoreconf -vif

  # we make the docs, and the Perl and Python bindings in the spec, 
  # not the library's Makefile (see the docs section below)
  %configure \
    --disable-documentation \
    --disable-html-docs \
    --disable-manpages \
    --disable-python-binding \
    --disable-perl-binding \
    --disable-static \
    --sbindir=%{_sbindir} YACC=bison 

  %make_build

  pushd language
    %{__make} perl/Makefile.PL

    pushd perl
      %{__perl} Makefile.PL INSTALLDIRS=vendor NO_PACKLIST=1 OPTIMIZE="%{optflags}"
      %make_build
    popd

    pushd python
      %pyproject_wheel
    popd
  popd # language
popd # %%{name}-user

%install
# build directory tree
install -d %{buildroot}%{_docdir}/%{name}
install -d %{buildroot}%{_mandir}/{man1,man3,man5,man8,mann}

install -d %{buildroot}%{guile_site}
install -d %{buildroot}%{tcl_sitearch}/%{name}

# userspace
pushd %{upstream_name}-user
  %make_install

  pushd language
    pushd guile
      install -p -m 0644 gpib.scm %{buildroot}%{guile_site}
    popd

    pushd perl
      %{__make} pure_install DESTDIR=%{buildroot}
    popd

    pushd python
      %pyproject_install
    popd

    pushd tcl
      mv %{buildroot}%{_libdir}/*_tcl* %{buildroot}%{tcl_sitearch}/%{name}
      install -p -m 0644 gpib.n %{buildroot}%{_mandir}/mann
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
# ... and static libraries for language bindings
rm -f %{buildroot}%{_libdir}/guile/1.8/extensions/*-guile.a
rm -f %{buildroot}%{tcl_sitearch}/%{name}/*_tcl.a

%check
pushd %{upstream_name}-user/language/perl
  %{__make} test LD_LIBRARY_PATH=%{buildroot}%{_libdir}
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

udevadm control --reload > /dev/null 2>&1 || :

# 'remove' or 'purge' are the possible names for foreign packages.
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

%{_libdir}/libgpib.so.%{soversion}
%{_libdir}/libgpib.so.%{soversion}.*

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

%exclude %{_mandir}/man3/*.3pm*


%files -n guile18-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/guile/README

%{_libdir}/guile/1.8/extensions/*-guile*.so*
%{guile_site}/*.scm


%files -n php-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING

%{php_extdir}/*.so*


%files -n python3-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/python/README
%{python3_sitearch}/Gpib.py
%{python3_sitearch}/__pycache__/Gpib.cpython-*.pyc
%{python3_sitearch}/gpib-1.0.dist-info/INSTALLER
%{python3_sitearch}/gpib-1.0.dist-info/METADATA
%{python3_sitearch}/gpib-1.0.dist-info/WHEEL
%{python3_sitearch}/gpib-1.0.dist-info/top_level.txt
%{python3_sitearch}/gpib.cpython-*-linux-gnu.so


%files -n perl-%{perlname}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/perl/README

%dir %{perl_vendorarch}/auto/%{perlname}

%{perl_vendorarch}/%{perlname}.pm
%{perl_vendorarch}/auto/%{perlname}/%{perlname}.*
%{perl_vendorarch}/auto/%{perlname}/autosplit.ix

%{_mandir}/man3/*.3pm*


%files -n tcl-%{name}
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING
%doc %{upstream_name}-user/language/tcl/README

%{tcl_sitearch}/%{name}

%{_mandir}/mann/gpib.n*


%files doc
%defattr(644,root,root,755)

%license %{upstream_name}-user/COPYING

%{_docdir}/%{name}


%changelog
%autochangelog

