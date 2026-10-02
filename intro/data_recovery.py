import argparse

parser = argparse.ArgumentParser(description="Read samples from an ADALM-Pluto")
parser.add_argument(
	"--uri",
	default="ip:192.168.2.1",
	help="libiio URI, for example ip:192.168.2.1 or serial:COM3,115200",
)

args = parser.parse_args()

try:
	import adi
except ModuleNotFoundError as error:
	raise SystemExit(
		"The 'adi' module is missing. Install it with: "
		"python -m pip install pyadi-iio pylibiio numpy matplotlib"
	) from error

sdr = adi.Pluto(uri=args.uri)
sdr.sample_rate = 2_000_000
sdr.rx_lo = 2_400_000_000
sdr.rx_rf_bandwidth = 2_000_000
data = sdr.rx()

print(data)








