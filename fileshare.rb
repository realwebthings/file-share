class Fileshare < Formula
  desc "Share files over WiFi"
  homepage "https://github.com/realwebthings/file-share"
  url "https://github.com/realwebthings/file-share/releases/download/v1.0.0/fileshare-universal.run"
  version "1.0.0"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"

  def install
    bin.install "fileshare-universal.run" => "fileshare-installer"
    
    (bin/"fileshare").write <<~EOS
      #!/bin/bash
      if [ ! -f "$HOME/.local/share/fileShare/fileshare" ]; then
        echo "Installing fileShare.app..."
        #{bin}/fileshare-installer
      fi
      exec "$HOME/.local/share/fileShare/fileshare" "$@"
    EOS
  end

  test do
    system "#{bin}/fileshare", "--help"
  end
end
