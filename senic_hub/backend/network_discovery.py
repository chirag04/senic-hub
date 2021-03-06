import importlib
import threading

from netdisco.philips_hue_nupnp import PHueNUPnPDiscovery
from netdisco.mdns import MDNS
from netdisco.ssdp import SSDP


class NetworkDiscovery(object):
    """
    Based on netdisco.discovery.NetworkDiscovery. This class only does
    discovery using SSDP & nUPNP which covers all the devices we want
    to support at the moment.

    """

    def __init__(self, whitelist):
        """
        Initialize the discovery.

        :param whitelist: list of devices to discover
        """
        self.whitelist = whitelist

        self.mdns = MDNS()
        self.phue = PHueNUPnPDiscovery()
        self.ssdp = SSDP()

        self._load_device_support()

        self.is_discovering = False

    def scan(self):
        """Start and tells scanners to scan."""
        if not self.is_discovering:
            self.is_discovering = True

        # Start all discovery processes in parallel
        mdns_thread = threading.Thread(target=self.mdns.start)
        mdns_thread.start()

        phue_thread = threading.Thread(target=self.phue.scan)
        phue_thread.start()

        ssdp_thread = threading.Thread(target=self.ssdp.scan)
        ssdp_thread.start()

        # Wait for all discovery processes to complete
        mdns_thread.join()
        phue_thread.join()
        ssdp_thread.join()

    def stop(self):
        """Turn discovery off."""
        if not self.is_discovering:
            return

        self.is_discovering = False

    def discover(self):
        """Return a list of discovered devices and services."""
        self._check_enabled()

        return [dis for dis, checker in self.discoverables.items()
                if checker.is_discovered()]

    def get_info(self, dis):
        """Get a list with the most important info about discovered type."""
        return self.discoverables[dis].get_info()

    def get_entries(self, dis):
        """Get a list with all info about a discovered type."""
        return self.discoverables[dis].get_entries()

    def _check_enabled(self):
        """Raise RuntimeError if discovery is disabled."""
        if not self.is_discovering:
            raise RuntimeError("NetworkDiscovery is disabled")

    def _load_device_support(self):
        """Load the devices and services that can be discovered."""
        self.discoverables = {}

        for device_name in self.whitelist:
            module_name = 'netdisco.discoverables.{}'.format(device_name)
            module = importlib.import_module(module_name)

            self.discoverables[device_name] = module.Discoverable(self)
