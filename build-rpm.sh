#!/bin/bash
# Build RPM package for FileShare Server (CentOS/RHEL/Fedora)

set -e

PACKAGE_NAME="fileshare-server"
VERSION="1.0.0"

echo "🔧 Building RPM package: ${PACKAGE_NAME}-${VERSION}.rpm"

# Create RPM build directory structure
RPM_DIR="$HOME/rpmbuild"
mkdir -p "$RPM_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create spec file
cat > "$RPM_DIR/SPECS/fileshare-server.spec" << EOF
Name:           fileshare-server
Version:        1.0.0
Release:        1%{?dist}
Summary:        Secure file sharing server for local networks
License:        MIT
URL:            https://github.com/yourusername/fileshare-server
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.8

%description
FileShare Server allows you to easily share files between your computer
and mobile devices over your local WiFi network. Features include secure
authentication, mobile-friendly interface, video streaming, and rate limiting.

%prep
%setup -q

%build
# Nothing to build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/share/fileshare
mkdir -p %{buildroot}/usr/bin

cp auth_server.py %{buildroot}/usr/share/fileshare/
cp remote_control.py %{buildroot}/usr/share/fileshare/
cp -r templates %{buildroot}/usr/share/fileshare/

cat > %{buildroot}/usr/bin/fileshare << 'WRAPPER'
#!/bin/bash
cd /usr/share/fileshare
python3 auth_server.py "\$@"
WRAPPER

chmod +x %{buildroot}/usr/bin/fileshare

%files
/usr/share/fileshare/
/usr/bin/fileshare

%changelog
* $(date '+%a %b %d %Y') Your Name <your.email@example.com> - 1.0.0-1
- Initial release
EOF

# Create source tarball
tar czf "$RPM_DIR/SOURCES/${PACKAGE_NAME}-${VERSION}.tar.gz" \
    --transform "s,^,${PACKAGE_NAME}-${VERSION}/," \
    auth_server.py remote_control.py templates/

# Build the RPM
rpmbuild -ba "$RPM_DIR/SPECS/fileshare-server.spec"

echo "✅ RPM package built in: $RPM_DIR/RPMS/noarch/"
echo ""
echo "📦 To install:"
echo "   sudo rpm -i $RPM_DIR/RPMS/noarch/${PACKAGE_NAME}-${VERSION}-1.*.rpm"
echo ""
echo "🚀 To run after installation:"
echo "   fileshare"