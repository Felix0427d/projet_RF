#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_root="$HOME/src/rf-project-radio-deps"

sudo apt-get update
sudo apt-get install -y \
  build-essential \
  cmake \
  git \
  gnuradio \
  gnuradio-dev \
  libad9361-dev \
  libboost-all-dev \
  libiio-dev \
  libspdlog-dev \
  libvolk-dev \
  pkg-config

mkdir -p "$source_root"

if [[ ! -d "$source_root/gr-ieee802-11/.git" ]]; then
  git clone --depth 1 --branch maint-3.10 \
    https://github.com/bastibl/gr-ieee802-11.git \
    "$source_root/gr-ieee802-11"
fi

if [[ ! -d "$source_root/gr-iio/.git" ]]; then
  git clone --depth 1 \
    https://github.com/analogdevicesinc/gr-iio.git \
    "$source_root/gr-iio"
fi

for module in gr-ieee802-11 gr-iio; do
  cmake -S "$source_root/$module" -B "$source_root/$module/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local
  cmake --build "$source_root/$module/build" --parallel
  sudo cmake --install "$source_root/$module/build"
done

sudo ldconfig
grcc -d "$project_dir" "$source_root/gr-ieee802-11/examples/wifi_phy_hier.grc"

echo "GNU Radio dependencies are ready. Run pluto_espnow_rx.py from labo1."