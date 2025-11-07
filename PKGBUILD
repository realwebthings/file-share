# Maintainer: FileShare <support@fileshare.com>
pkgname=fileshare-bin
pkgver=1.0.0
pkgrel=1
pkgdesc="Share files over WiFi"
arch=('x86_64')
url="https://github.com/realwebthings/file-share"
license=('MIT')
depends=('python')
source=("https://github.com/realwebthings/file-share/releases/download/v${pkgver}/fileshare-universal.run")
sha256sums=('SKIP')

package() {
    install -Dm755 "$srcdir/fileshare-universal.run" "$pkgdir/usr/bin/fileshare-installer"
    
    # Create wrapper
    cat > "$pkgdir/usr/bin/fileshare" << 'EOF'
#!/bin/bash
if [ ! -f "$HOME/.local/share/fileShare/fileshare" ]; then
    echo "Installing fileShare.app..."
    /usr/bin/fileshare-installer
fi
exec "$HOME/.local/share/fileShare/fileshare" "$@"
EOF
    chmod +x "$pkgdir/usr/bin/fileshare"
}
