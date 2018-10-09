%global tvheadend_user %{name}
%global tvheadend_group video

Name:           tvheadend
Version:        4.2.7
Release:        1%{?dist}
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
BuildRequires:  python3-devel
BuildRequires:  systemd
Requires:       bzip2
Requires:       dtv-scan-tables
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


%prep
%autosetup -p 0

# Delete bundled system headers
rm -r vendor/{dvb-api,include}/


%build
# Use touch to be sure that configure, after being patched, is still older than
# generated .config.mk file (otherwise the build fails)
# touch -r Makefile configure
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
    --enable-libsystemd_daemon
%make_build V=1 PYTHON=%{__python3}


%install
%make_install

install -Dpm 0644 rpm/%{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -Dpm 0644 rpm/%{name}.sysconfig $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/%{name}

install -dm 0755 $RPM_BUILD_ROOT%{_sharedstatedir}/%{name}/

# Fix permissions
chmod 0644 $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1

# Drop bundled Ext JS resources not required by Tvheadend UI
pushd $RPM_BUILD_ROOT%{_datadir}/%{name}/src/webui/static/extjs/
mv examples/ux/images/ examples_ux_images
rm -r *.js adapter/ examples/ resources/images/{vista,yourtheme}/
install -dm 0755 examples/ux/
mv examples_ux_images/ examples/ux/images
popd


%pre
getent passwd %{tvheadend_user} >/dev/null || useradd -r -g %{tvheadend_group} -d %{_sharedstatedir}/%{name}/ -s /sbin/nologin -c "%{name} daemon account" %{name}
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


%changelog
* Tue Oct 09 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.7-1
- Update to 4.2.7
- Remove patches merges upstream
- Use Python 3 for build

* Sun Aug 19 2018 Leigh Scott <leigh123linux@googlemail.com> - 4.2.6-3
- Rebuilt for Fedora 29 Mass Rebuild binutils issue

* Fri Jul 27 2018 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 4.2.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Mar 27 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.6-1
- Update to 4.2.6

* Sat Mar 17 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.5-7
- Add explicite Requires on tar and bzip2 (required by Tvheadend for
  configuration backups)

* Thu Mar 08 2018 RPM Fusion Release Engineering <leigh123linux@googlemail.com> - 4.2.5-6
- Rebuilt for new ffmpeg snapshot

* Thu Mar 08 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.5-5
- Fix build with GCC >= 8
- Call python2 instead of python during build

* Thu Mar 01 2018 RPM Fusion Release Engineering <leigh123linux@googlemail.com> - 4.2.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 23 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.5-3
- Fix build with FFmpeg 3.5

* Thu Jan 18 2018 Leigh Scott <leigh123linux@googlemail.com> - 4.2.5-2
- Rebuilt for ffmpeg-3.5 git

* Sun Jan 07 2018 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.5-1
- Update to 4.2.5

* Thu Oct 19 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.4-1
- Update to 4.2.4

* Thu Aug 31 2017 RPM Fusion Release Engineering <kwizart@rpmfusion.org> - 4.2.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jul 03 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.3-1
- Update to 4.2.3

* Thu Jun 01 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.2-2
- Fix system DTV scan tables path

* Tue May 23 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.2-1
- Update to 4.2.2
- Drop patch for GCC7 (merged upstream)

* Sun Apr 30 2017 Leigh Scott <leigh123linux@googlemail.com> - 4.2.1-2
- Rebuild for ffmpeg update

* Sun Apr 23 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.2.1-1
- Update to 4.2.1

* Wed Apr 12 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.10-1
- Update to 4.0.10

* Sat Mar 25 2017 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-5
- Fix build with GCC 7
- Enable DVBCSA support

* Mon Mar 20 2017 RPM Fusion Release Engineering <kwizart@rpmfusion.org> - 4.0.9-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Aug 09 2016 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-3
- Merge all FFmpeg patches into a single one

* Tue Aug 09 2016 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-2
- Fix build with FFmpeg 3.1

* Thu Jul 28 2016 Mohamed El Morabity <melmorabity@fedoraproject.org> - 4.0.9-1
- Initial RPM release
