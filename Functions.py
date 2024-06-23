import psutil


def close_all_edge_instances():
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            if process.info['name'] == 'msedge.exe' or process.info['name'] == 'msedgedriver.exe':
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def close_all_chrome_instances():
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            if process.info['name'] == 'chrome.exe' or process.info['name'] == 'chromedriver.exe':
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def close_all_nordvpn_instances():
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            if process.info['name'] == 'nordvpn.exe' or process.info['name'] == 'nordvpn-service.exe':
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


        