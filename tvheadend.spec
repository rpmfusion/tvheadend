%global tvheadend_user %{name}
%global tvheadend_group video

%if 0%{?fedora} || 0%{?rhel} > 7
%global _with_python3 1
%global __python %{__python3}
%global python_sitearch %{python3_sitearch}
%else
%global __python %{__python2}
%global python_sitearch %{python2_sitearch}
%endif

%if 0%{?fedora} && 0%{?fedora} < 30
%global _with_python2 1
%endif

%if 0%{?rhel} && 0%{?rhel} < 8
%global _with_python2 1
%endif

Name:           tvheadend
Version:        4.2.8
Release:        7%{?dist}
Summary:        TV streaming server and digital video recorder

License:        GPLv3+
URL:            https://tvheadend.org/
Source0:        https://github.com/tvheadend/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz
# Fix build with hdhomerun
Patch0:         %{name}-4.2.1-hdhomerun.patch
# Fix systemd service and configuration:
# - Fix daemon group (use video to access DVB devices)
# - Add -C option to allow UI access without login at first run
Patch1:         %{name}-4.2.7-service.patch
# Use system queue.h header
Patch2:         %{name}-4.0.9-use_system_queue.patch
# Fix system DTV scan tables path
Patch3:         %{name}-4.2.2-dtv_scan_tables.patch
# Enforcing system crypto policies, see
# https://fedoraproject.org/wiki/Packaging:CryptoPolicies
Patch4:         %{name}-4.2.1-crypto_policies.patch
# Python 3 fixes for Python bindings
Patch5:         %{name}-4.2.7-python3.patch
# Fix build with GCC 9
Patch6:         %{name}-4.2.8-gcc9.patch
# Fix build with hdhomerun >= 20190621
Patch7:         %{name}-4.2.8-hdhomerun20190621.patch

BuildRequires:  bzip2
BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  gzip
BuildRequires:  hdhomerun-devel
BuildRequires:  libdvbcsa-devel
BuildRequires:  pkgconfig(avahi-client)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libavformat)
BuildRequires:  pkgconfig(libavresample)
BuildRequires:  pkgconfig(libavutil)
BuildRequires:  pkgconfig(libswresample)
BuildRequires:  pkgconfig(libswscale)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(liburiparser)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)
%if 0%{?_with_python3}
BuildRequires:  python3-devel
BuildRequires:  python3-rcssmin
BuildRequires:  python3-rjsmin
%else
# Needed on EL7 (python2-only)
BuildRequires:  python2-rcssmin
BuildRequires:  python2-rjsmin
%endif
%if 0%{?_with_python2}
# Needed everwhere but in f30+
BuildRequires:  python2-devel
%endif
BuildRequires:  systemd
Requires:       bzip2
%if 0%{?fedora}
Requires:       dtv-scan-tables
%endif
Requires:       tar
%{?systemd_requires}
Provides:       bundled(extjs) = 3.4.1.1

%description
Tvheadend is a TV streaming server and recorder supporting DVB-S, DVB-S2, DVB-C,
DVB-T, ATSC, IPTV, SAT>IP and HDHomeRun as input sources.

Tvheadend offers the HTTP (VLC, MPlayer), HTSP (Kodi, Movian) and SAT>IP
streaming.

Multiple EPG sources are supported (over-the-air DVB and ATSC including OpenTV
DVB extensions, XMLTV, PyXML).

The Analog video (V4L) is supported directly up to version 3.4. In recent
version, the pipe:// source (in IPTV network) might be used to obtain the
MPEG-TS stream generated by ffmpeg/libav from a V4L device.


%if 0%{?_with_python2}
%package -n python2-tvh
Summary:        HTSP client for Python
BuildArch:      noarch

%description -n python2-tvh
%{summary}.
%endif


%if 0%{?_with_python3}
%package -n python3-tvh
Summary:        HTSP client for Python
BuildArch:      noarch

%description -n python3-tvh
%{summary}.
%endif


%prep
%autosetup -p0

# Delete bundled system headers and tools
rm -r vendor/{dvb-api,include,rcssmin-*,rjsmin-*}/

# Remove shebang
for i in lib/py/tvh/*.py; do
    sed '1{\@^#!/usr/bin/env python@d}' $i >$i.new && \
    touch -r $i $i.new && \
    mv $i.new $i
done


%build
# https://github.com/FFmpeg/FFmpeg/commit/4361293
# Force -fcommon until code fully supports GCC 10
export CFLAGS="$RPM_OPT_FLAGS -Wno-attributes -fcommon"
echo "%{version}-%{release}" >rpm/version
# Note: --disable-lib* correspond to options to build bundled FFmpeg
%configure \
    --disable-dvbscan \
    --disable-ffmpeg_static \
    --disable-hdhomerun_static \
    --disable-libfdkaac \
    --disable-libfdkaac_static \
    --disable-libtheora \
    --disable-libtheora_static \
    --disable-libvorbis \
    --disable-libvorbis_static \
    --disable-libvpx \
    --disable-libvpx_static \
    --disable-libx264 \
    --disable-libx264_static \
    --disable-libx265 \
    --disable-libx265_static \
    --enable-dvbcsa \
    --enable-hdhomerun_client \
    --enable-libsystemd_daemon \
    --python=%{__python}

%make_build \
    V=1 \
    RUN_CSS="%{__python} %{python_sitearch}/rcssmin.py" \
    RUN_JS="%{__python} %{python_sitearch}/rjsmin.py"


%install
%make_install

install -Dpm 0644 rpm/%{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -Dpm 0644 rpm/%{name}.sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}

install -dm 0755 $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}/

# Install Python bindings
%if 0%{?_with_python2}
install -dm 0755 $RPM_BUILD_ROOT%{python2_sitelib}/
cp -a lib/py/tvh/ $RPM_BUILD_ROOT%{python2_sitelib}/
%endif
%if 0%{?_with_python3}
install -dm 0755 $RPM_BUILD_ROOT%{python3_sitelib}/
cp -a lib/py/tvh/ $RPM_BUILD_ROOT%{python3_sitelib}/
%endif

# Fix permissions
chmod 0644 $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1


%pre
getent passwd %{tvheadend_user} >/dev/null || \
    useradd -r -g %{tvheadend_group} -d %{_sharedstatedir}/%{name}/ -s /sbin/nologin -c "%{name} daemon account" %{name}
exit 0


%post
%systemd_post %{name}.service


%preun
%systemd_preun %{name}.service


%postun
%systemd_postun_with_restart %{name}.service


%files
%doc CONTRIBUTING.md README.md
%license LICENSE.md licenses/gpl-3.0.txt
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(-,%{tvheadend_user},%{tvheadend_group}) %dir %{_sharedstatedir}/%{tvheadend_user}/
%{_mandir}/man1/*.1.*


%if 0%{?_with_python2}
%files -n python2-tvh
%license LICENSE.md licenses/gpl-3.0.txt
%{python2_sitelib}/tvh/
%endif


%if 0%{?_with_python3}
%files -n python3-tvh
%license LICENSE.md licenses/gpl-3.0.txt
%{python3_sitelib}/tvh/
%endif


%changelog
* Tue Mar 10 2020 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.8-7
- Fix build with hdhomerun >= 20190621
- Disable -fno-common flag to allow building with GCC 10

* Wed Feb 05 2020 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.8-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Sat Aug 24 2019 Leigh Scott <leigh123linux@gmail.com> - 4.2.8-5
- Rebuild for python-3.8

* Wed Aug 07 2019 Leigh Scott <leigh123linux@gmail.com> - 4.2.8-4
- Rebuild for new ffmpeg version

* Tue Mar 12 2019 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.8-3
- Fix build with GCC 9

* Mon Mar 04 2019 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Jan 16 2019 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.8-1
- Update to 4.2.8

* Fri Dec 14 2018 Nicolas Chauvet <kwizart@gmail.com> - 4.2.7-4
- Rework for python2/3

* Sat Dec 08 2018 Nicolas Chauvet <kwizart@gmail.com> - 4.2.7-3
- Avoid dtv-scan-tables on non-fedora for now

* Sat Nov 17 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.7-2
- Use system versions of rcssmin and rjsmin during build
- Install Python bindings

* Tue Oct 09 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.7-1
- Update to 4.2.7
- Remove patches merges upstream
- Use Python 3 for build
