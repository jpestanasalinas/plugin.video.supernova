import sys
import platform

from kodi_six import xbmc

from resources.site_packages.supernova.addon import ADDON
from resources.site_packages.supernova.logger import log


def get_platform():
    try:
        binary_platform = ADDON.getSetting("binary_platform")
    except:
        binary_platform = "auto"
        pass

    build = xbmc.getInfoLabel("System.BuildVersion")
    kodi_version = int(build.split()[0][:2])

    if binary_platform and "auto" not in binary_platform.lower():
        custom = binary_platform.split('_')
        if len(custom) > 1:
            return {
                "os": custom[0],
                "arch": custom[1],
                "fork": True,
                "version": "",
                "kodi": kodi_version,
                "build": build
            }

    ret = {
        "auto_arch": sys.maxsize > 2 ** 32 and "64-bit" or "32-bit",
        "arch": sys.maxsize > 2 ** 32 and "x64" or "x86",
        "os": "",
        "version": "",
        "kodi": kodi_version,
        "build": build,
        "fork": True,
        "machine": "",
        "system": "",
        "platform": ""
    }

    try:
        ret["os"] = platform.release()
    except:
        pass

    try:
        ret["machine"] = platform.machine()
    except:
        # Default 'machine' for Android can be 'arm'
        if xbmc.getCondVisibility("system.platform.android"):
            ret["machine"] = "arm"
        pass

    try:
        ret["system"] = platform.system()
    except:
        pass

    try:
        ret["platform"] = platform.platform()
    except:
        pass

    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in ret["machine"].lower() or "aarch" in ret["machine"].lower():
            ret["arch"] = "arm"
            if "64" in ret["machine"] and ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"

        if "aarch" in ret["machine"].lower() or "arm64" in ret["machine"].lower():
            if xbmc.getCondVisibility("system.platform.linux.raspberrypi"):
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "32-bit":
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
            # elif platform.architecture()[0].startswith("32"):
            #     ret["arch"] = "armv6"
            else:
                ret["arch"] = "armv7"
        elif "armv7" in ret["machine"]:
            ret["arch"] = "armv7"
        elif "arm" in ret["machine"]:
            cpuarch = ""
            if "aarch" in ret["machine"].lower() or "arm" in ret["machine"].lower():
                info = cpuinfo()
                for proc in info.keys():
                    log.info("CPU: %s=%s" % (proc, info[proc]))
                    model = ""
                    if "model name" in info[proc]:
                        model = info[proc]["model name"].lower()
                    elif "Processor" in info[proc]:
                        model = info[proc]["Processor"].lower()

                    if model:
                        log.info("Exploring model: %s" % model)
                        if "aarch" in model or "arm64" in model or "v8l" in model:
                            cpuarch = "arm64"
                        elif "armv7" in model or "v7l" in model:
                            cpuarch = "armv7"
                        break

            if cpuarch:
                log.info("Using CPU info arch: %s" % cpuarch)
                ret["arch"] = cpuarch
            else:
                ret["arch"] = "armv6"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        ret["os"] = "windows"
        ret["arch"] = "x64"
        ret["fork"] = False
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "windows"
        if ret["machine"].endswith('64'):
            ret["arch"] = "x64"
    elif ret["system"] == "Darwin":
        ret["os"] = "darwin"
        ret["arch"] = "x64"

        if "AppleTV" in ret["platform"]:
            ret["os"] = "ios"
            ret["arch"] = "armv7"
            ret["fork"] = False
            if "64bit" in ret["platform"]:
                ret["arch"] = "arm64"
        elif xbmc.getCondVisibility("system.platform.ios"):
            ret["os"] = "ios"
            ret["arch"] = "armv7"
            ret["fork"] = False
            if "64bit" in ret["platform"]:
                ret["arch"] = "arm64"

    # elif xbmc.getCondVisibility("system.platform.osx"):
    #     ret["os"] = "darwin"
    #     ret["arch"] = "x64"
    # elif xbmc.getCondVisibility("system.platform.ios"):
    #     ret["os"] = "ios"
    #     ret["arch"] = "armv7"
    return ret

def linux_distribution():
    try:
        return platform.linux_distribution()
    except:
        return "N/A"

def cpuinfo():
    cpuinfo = {}
    procinfo = {}
    nprocs = 0
    with open('/proc/cpuinfo') as f:
        for line in f:
            if not line.strip():
                cpuinfo['proc%s' % nprocs] = procinfo
                nprocs = nprocs + 1
            else:
                if len(line.split(':')) == 2:
                    procinfo[line.split(':')[0].strip()] = line.split(':')[1].strip()
                else:
                    procinfo[line.split(':')[0].strip()] = ''
    return cpuinfo

def dump_version(ret):
    try:
        p = platform.platform()
    except:
        p = "Could not detect"

    try:
        log.info("""Python version: %s
        dist: %s
        linux_distribution: %s
        system: %s
        machine: %s
        platform: %s
        uname: %s
        version: %s
        mac_ver: %s
        """ % (
            sys.version.split('\n'),
            str(platform.dist()),
            linux_distribution(),
            platform.system(),
            platform.machine(),
            p,
            platform.uname(),
            platform.version(),
            platform.mac_ver()
        ))
    except:
        if ret is not None:
            log.info("Cannot write detection info. Ret: %s" % (repr(ret)))
        pass


PLATFORM = get_platform()
