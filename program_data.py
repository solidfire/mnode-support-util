# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# global vaiarbles
#============================================================
class ProgramData():
    # Define the used variables
    def __init__(self, args):
        self.UTIL_VERSION = "2.5"
        self.PAYLOAD = {}
        self.UPDATEFILE = args.updatefile
        # token 
        self.TOKEN = "none"
        self.NEW_TOKEN = False
        self.TOKEN_LIFE = int()
        self.HEADER_READ = {}
        self.HEADER_WRITE = {}
        # mnode endpoint
        self.STORAGE_USER = args.stuser
        self.STORAGE_PASSWD = args.stpw
        self.PARENT_ID = ""
        self.CURRENT_ASSET_JSON = []
        self.JSON_DATA = []
        self.ASSET_TYPE = ["compute", "hardware", "controller", "storage"]
        self.ASSET_URL_TYPE = ["compute-nodes", "hardware-nodes", "controllers", "storage-clusters"]
        self.SERVICE_STATUS = "none"
        self.BACKUP_PREFIX = "/var/log/AssetBackup"
        # REVISIT - ONLY USED IN __main__.py
        self.COMPUTE_TMPLT = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "ESXi Host"}
        self.HARDWARE_TMPLT = {"config": {}, "hardware_tag": "string", "host_name": "string", "ip": "x.x.x.x", "type": "BMC"}
        self.CONTROLLER_TMPLT = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "type": "vCenter"}
        self.STORAGE_TMPLT = {"config": {}, "host_name": "string", "ip": "x.x.x.x", "ssl_certificate": "REMOVE IF NOT USED"}
        self.SERVICE_LIST = "none"
        self.SETTINGS = "none"
        self.ABOUT = "none"
        self.URL = ("https://{}".format(args.mnodeip))
        self.MNODEIP = "none"
        self.USERID = "none"
        # inventory endpoint
        self.INVENTORY_AUTHORATIVE_CLUSTER = "none"
        self.COMPUTE_UPGRADE = []
        self.STORAGE_UPGRADE = []
        # storage endpoint
        self.SELECTED_NODES = []
        self.CLUSTERS = []
        self.CHECK_AUTH = []  
        self.HEALTH_CHECK = []
        self.STORAGE_ID = "none"
        self.UPGRADE_ID = "none"        
        self.UPGRADE_STATUS_MESSAGE = "none"
        self.UPGRADE_ACTION = "none"
        self.UPGRADE_OPTION = "none"
        self.STORAGE_HEALTHCHECK_TASK = "none"
        # hardware endpoint
        self.HARDWARE = []

        # compute endpoint
        self.CONTROLLERS = []
        self.CONTROLLER_ID = "none"
        self.CLUSTER_ID = "none"
        self.COMPUTE_HEALTHCHECK_TASK = []
        # support items
        self.SUPPORT_DIR = "/var/log/mnode-support/"
        self.TIME_STAMP = "none"
        self.AUTH_CONFIG = []
        self.TOKEN_CLIENT = "mnode-client"
        # docker stuff
        self.CONTAINER_LIST = []
        self.DOCKER_PS = []
        self.DOCKER_INSPECT = []
        self.DOCKER_SERVICE = []
        self.DOCKER_VOLUME = []
        self.DOCKER_STATS = []
        self.DOCKER_NETWORK = []
        self.DOCKER_LOGS = []
        # Element upgrades
        self.STORAGE_ELEMENT_UPGRADE_TARGET = "none"
        self.STORAGE_ELEMENT_UPGRADE_PACKAGE = "none"
        self.STORAGE_UPGRADE_LOG = "none"
        self.UPGRADE_TASK_ID = "none"

