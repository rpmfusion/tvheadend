%global commit 26ec161fb3c903f8b0d0be8b54d1b67c596fb829
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global commitdate 20241008

# https://tvheadend.org/issues/6026
%global _lto_cflags %nil

# https://fedoraproject.org/wiki/Changes/OpensslDeprecateEngine
%if 0%{?fedora} > 40
%global _preprocessor_defines %{?_preprocessor_defines} -DOPENSSL_NO_ENGINE
%endif

Name:           tvheadend
Version:        4.3^%{commitdate}git%{shortcommit}
Release:        9%{?dist}
Summary:        TV streaming server and digital video recorder

# - Source code is GPL-3.0-or-later
# - Silk icons in vendor/famfamsilk/ are CC-BY-2.5
# - Noto icons in vendor/noto/ are ASL
License:        GPL-3.0-or-later and CC-BY-2.5 and Apache-2.0
URL:            https://tvheadend.org/
Source0:        https://github.com/%{name}/%{name}/archive/%{shortcommit}/%{name}-%{shortcommit}.tar.gz
Source1:        %{name}.sysusers
# Use system queue.h header
Patch0:         %{name}-4.3-use_system_queue.patch
# Fix build with hdhomerun
Patch1:         %{name}-4.3-hdhomerun.patch
# Python 3 fixes for Python bindings
Patch2:         %{name}-4.3-python3.patch
# Fix systemd service and configuration:
# - Fix daemon group (use video to access DVB devices)
# - Add -C option to allow UI access without login at first run
Patch3:         %{name}-4.3-service.patch
# Fix system DTV scan tables path
Patch4:         %{name}-4.3-dtv_scan_tables.patch
# Enforcing system crypto policies, see
# https://fedoraproject.org/wiki/Packaging:CryptoPolicies
Patch5:         %{name}-4.3-crypto_policies.patch

BuildRequires:  bzip2
BuildRequires:  gcc
BuildRequires:  gettext
BuildRequires:  gzip
BuildRequires:  hdhomerun-devel
BuildRequires:  libdvbcsa-devel
BuildRequires:  make
BuildRequires:  pkgconfig(avahi-client)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libavcodec)
BuildRequires:  pkgconfig(libavfilter)
BuildRequires:  pkgconfig(libavformat)
BuildRequires:  pkgconfig(libavutil)
BuildRequires:  pkgconfig(libpcre2-8)
BuildRequires:  pkgconfig(libswresample)
BuildRequires:  pkgconfig(libswscale)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(liburiparser)
BuildRequires:  pkgconfig(libva)
BuildRequires:  pkgconfig(libva-drm)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(opus)
BuildRequires:  pkgconfig(vpx)
BuildRequires:  pkgconfig(x264)
BuildRequires:  pkgconfig(x265)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  python3-devel
BuildRequires:  %{py3_dist rcssmin}
BuildRequires:  %{py3_dist rjsmin}
BuildRequires:  systemd-rpm-macros
Requires:       bzip2
Requires:       tar
Requires:       %{py3_dist requests}
Requires:       dtv-scan-tables
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


%package -n python3-tvh
Summary:        HTSP client for Python
BuildArch:      noarch
%py_provides python3-tvh

%description -n python3-tvh
%{summary}.


%prep
%autosetup -n %{name}-%{commit} -p0

# Delete bundled system headers and tools
rm -r vendor/{dvb-api,include,rcssmin-*,rjsmin-*}/

# Remove shebang
for i in lib/py/tvh/*.py; do
    [[ $i =~ /tv_meta_ ]] && continue
    sed '1{\@^#!\s*/usr/bin/env\s\+python@d}' $i >$i.new && \
    touch -r $i $i.new && \
    mv $i.new $i
done


%build
echo "%{version}-%{release}" >rpm/version
%configure \
    --disable-dvbscan \
    --disable-libfdkaac_static \
    --disable-ffmpeg_static \
    --disable-hdhomerun_static \
    --disable-libfdkaac_static \
    --disable-libopus_static \
    --disable-libtheora_static \
    --disable-libvorbis_static \
    --disable-libvpx_static \
    --disable-libx264_static \
    --disable-libx265_static \
    --enable-libfdkaac \
    --enable-hdhomerun_client \
    --enable-libsystemd_daemon \
    --python=%{python3}

%make_build \
    V=1 \
    RUN_CSS="%{python3} %{python3_sitearch}/rcssmin.py" \
    RUN_JS="%{python3} %{python3_sitearch}/rjsmin.py"


%install
%make_install

install -Dpm 0644 %{SOURCE1} $RPM_BUILD_ROOT%{_sysusersdir}/%{name}.conf

%py3_shebang_fix $RPM_BUILD_ROOT%{_bindir}/{*.py,tvhmeta}
chmod 0755 $RPM_BUILD_ROOT%{_bindir}/{*.py,tvhmeta}

install -Dpm 0644 rpm/%{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -Dpm 0644 rpm/%{name}.sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}

install -dm 0755 $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}/

# Install Python bindings
install -dm 0755 $RPM_BUILD_ROOT%{python3_sitelib}/
cp -a lib/py/tvh/ $RPM_BUILD_ROOT%{python3_sitelib}/
rm $RPM_BUILD_ROOT%{python3_sitelib}/tvh/tv_meta_*.py

# Fix permissions
chmod 0644 $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1


%check
%py3_check_import tvh


%pre
%sysusers_create_compat %{SOURCE1}


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
%{_bindir}/tv_meta_tmdb.py
%{_bindir}/tv_meta_tvdb.py
%{_bindir}/tvhmeta
%{_datadir}/%{name}/
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(-,%{name},video) %dir %{_sharedstatedir}/%{name}/
%{_sysusersdir}/%{name}.conf
%{_mandir}/man1/*.1.*


%files -n python3-tvh
%license LICENSE.md licenses/gpl-3.0.txt
%{python3_sitelib}/tvh/


%changelog
* Sun Oct 13 2024 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3^20241008git26ec161-9
- Update to latest snapshot

* Sun Aug 11 2024 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3^20240810git49ac938-8
- Update to latest snapshot
- Fix FTBFS because of OpenSSL engine depreciation

* Fri Aug 02 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.3^20240111gitc9b38a8-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jun 13 2024 Leigh Scott <leigh123linux@gmail.com> - 4.3^20240111gitc9b38a8-6
- Rebuilt for Python 3.13

* Sun Feb 04 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.3^20240111gitc9b38a8-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Fri Jan 12 2024 Sérgio Basto <sergio@serjux.com> - 4.3^20240111gitc9b38a8-4
- Update to latest snapshot
- Fix rfbz #6840 Crash on Fedora 38 and Fedora 39

* Wed Aug 02 2023 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.3^20230408gitf32c7c5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sat Jul 08 2023 Leigh Scott <leigh123linux@gmail.com> - 4.3^20230408gitf32c7c5-2
- Rebuilt for Python 3.12

* Tue Apr 04 2023 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3^20230408gitf32c7c5-1
- Update to latest snapshot
- Fix build with FFmpeg 6
- Switch to SPDX license identifiers

* Wed Aug 17 2022 Leigh Scott <leigh123linux@gmail.com> - 4.3-9.20220330git2bf1629
- Set pkgconfig path for compat-ffmpeg4

* Mon Aug 08 2022 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.3-8.20220330git2bf1629
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild and ffmpeg
  5.1

* Sat Jun 25 2022 Robert-André Mauchin <zebob.m@gmail.com> - 4.3-7.20220330git2bf1629
- Rebuilt for Python 3.11

* Mon Apr 04 2022 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3-6.20220330git2bf1629
- Update to latest snapshot
- Add workaround to build with GCC 12
- Force build with FFmpeg 4.0

* Wed Feb 09 2022 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 4.3-5.20210724git6efa411
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Fri Nov 12 2021 Leigh Scott <leigh123linux@gmail.com> - 4.3-4.20210724git6efa411
- Rebuilt for new ffmpeg snapshot

* Tue Aug 03 2021 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.3-3.20210724git6efa411
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jul 27 2021 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3-3.20210724git6efa411
- Update to latest snapshot
- Drop any dependency to libavresample (fix RHBZ #5352)

* Sat Jul 10 2021 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.3-1.20210612giteb59284
- Update to latest snapshot

* Tue Jun 15 2021 Leigh Scott <leigh123linux@gmail.com> - 4.2.8-15
- Rebuild for python-3.10

* Thu Feb 04 2021 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.8-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Fri Jan  1 2021 Leigh Scott <leigh123linux@gmail.com> - 4.2.8-13
- Rebuilt for new ffmpeg snapshot

* Thu Aug 20 2020 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.8-12
- Fix F33 FTBFS

* Tue Aug 18 2020 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.8-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jun 03 2020 Sérgio Basto <sergio@serjux.com> - 4.2.8-10
- Fix building with -fno-common (default from GCC 10)

* Sat May 30 2020 Leigh Scott <leigh123linux@gmail.com> - 4.2.8-9
- Rebuild for python-3.9

* Wed Mar 11 2020 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.8-8
- Fix build with hdhomerun >= 20190621
- Fix build with GCC 10

* Sat Feb 22 2020 RPM Fusion Release Engineering <leigh123linux@googlemail.com> - 4.2.8-7
- Rebuild for ffmpeg-4.3 git

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
