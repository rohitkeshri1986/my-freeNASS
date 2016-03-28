import ConfigParser
import hashlib
import logging
import os
import sys
import tempfile
import time
import urllib2
import httplib
import socket
import ssl

from . import Avatar, UPDATE_SERVER, MASTER_UPDATE_SERVER
import Exceptions
import Installer
import Train
import Package
import Manifest

from stat import (
    S_ISDIR, S_ISCHR, S_ISBLK, S_ISREG, S_ISFIFO, S_ISLNK, S_ISSOCK,
    S_IMODE
)

VERIFY_SKIP_PATHS = [
    '/var/', '/etc', '/dev', '/conf/base/etc/master.passwd', '/compat/linux/proc',
    '/boot/zfs/zpool.cache', '/boot/device.hints', '/usr/share/man/whatis',
    '/usr/local/share/smartmontools/drivedb.h', '/usr/local/lib/perl5/5.16/man/whatis',
]

CONFIG_DEFAULT = "Defaults"
CONFIG_SEARCH = "Search"
CONFIG_SERVER = "update_server"

UPDATE_SERVER_NAME_KEY = "name"
UPDATE_SERVER_MASTER_KEY = "master"
UPDATE_SERVER_URL_KEY = "url"
UPDATE_SERVER_SIGNED_KEY = "signing"

TRAIN_DESC_KEY = "Descripton"
TRAIN_SEQ_KEY = "Sequence"
TRAIN_CHECKED_KEY = "LastChecked"

log = logging.getLogger('freenasOS.Configuration')

# Change this for release
# Need to change search code since it isn't really
# searching any longer.
# We may want to use a different update server for
# TrueNAS.
#UPDATE_SERVER = "http://beta-update.freenas.org/" + Avatar()
SEARCH_LOCATIONS = ["http://update.freenas.org/" + Avatar()]

# List of trains
TRAIN_FILE = "trains.txt"

def ChecksumFile(fobj):
    # Produce a SHA256 checksum of a file.
    # Read it in chunk
    def readchunk():
        chunksize = 1024 * 1024
        return fobj.read(chunksize)
    hash = hashlib.sha256()
    fobj.seek(0)
    for piece in iter(readchunk, ''):
        hash.update(piece)
    fobj.seek(0)
    return hash.hexdigest()

    
def TryOpenFile(path):
    try:
        f = open(path, "r")
    except:
        return None
    else:
        return f

# This code taken from
# http://stackoverflow.com/questions/1087227/validate-ssl-certificates-with-python

class InvalidCertificateException(httplib.HTTPException, urllib2.URLError):
    def __init__(self, host, cert, reason):
        httplib.HTTPException.__init__(self)
        self.host = host
        self.cert = cert
        self.reason = reason

    def __str__(self):
        return ('Host %s returned an invalid certificate (%s) %s\n' %
                (self.host, self.reason, self.cert))

class CertValidatingHTTPSConnection(httplib.HTTPConnection):
    default_port = httplib.HTTPS_PORT

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                             ca_certs=None, strict=None, **kwargs):
        httplib.HTTPConnection.__init__(self, host, port, strict, **kwargs)
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_certs = ca_certs
        if self.ca_certs:
            self.cert_reqs = ssl.CERT_REQUIRED
        else:
            self.cert_reqs = ssl.CERT_NONE

    def _GetValidHostsForCert(self, cert):
        if 'subjectAltName' in cert:
            return [x[1] for x in cert['subjectAltName']
                         if x[0].lower() == 'dns']
        else:
            return [x[0][1] for x in cert['subject']
                            if x[0][0].lower() == 'commonname']

    def _ValidateCertificateHostname(self, cert, hostname):
        import re
        hosts = self._GetValidHostsForCert(cert)
        for host in hosts:
            host_re = host.replace('.', '\.').replace('*', '[^.]*')
            if re.search('^%s$' % (host_re,), hostname, re.I):
                return True
        return False

    def connect(self):
        sock = socket.create_connection((self.host, self.port))
        self.sock = ssl.wrap_socket(sock, keyfile=self.key_file,
                                          certfile=self.cert_file,
                                          cert_reqs=self.cert_reqs,
                                          ca_certs=self.ca_certs)
        if self.cert_reqs & ssl.CERT_REQUIRED:
            cert = self.sock.getpeercert()
            hostname = self.host.split(':', 0)[0]
            if not self._ValidateCertificateHostname(cert, hostname):
                raise InvalidCertificateException(hostname, cert,
                                                  'hostname mismatch')


class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    def __init__(self, **kwargs):
        urllib2.AbstractHTTPHandler.__init__(self)
        self._connection_args = kwargs

    def https_open(self, req):
        def http_class_wrapper(host, **kwargs):
            full_kwargs = dict(self._connection_args)
            full_kwargs.update(kwargs)
            return CertValidatingHTTPSConnection(host, **full_kwargs)

        try:
            return self.do_open(http_class_wrapper, req)
        except urllib2.URLError, e:
            if type(e.reason) == ssl.SSLError and e.reason.args[0] == 1:
                raise InvalidCertificateException(req.host, '',
                                                  e.reason.args[1])
            raise

    https_request = urllib2.HTTPSHandler.do_request_


class PackageDB:
#    DB_NAME = "var/db/ix/freenas-db"
    DB_NAME = "data/pkgdb/freenas-db"
    __db_path = None
    __db_root = ""
    __conn = None
    __close = True

    def __init__(self, root = "", create = True):
        if root is None:
            root = ""
        self.__db_root = root
        self.__db_path = self.__db_root + "/" + PackageDB.DB_NAME
        if os.path.exists(os.path.dirname(self.__db_path)) == False:
            if create is False:
                raise Exception("Cannot connect to database file %s" % self.__db_path)
            log.debug("Need to create %s", os.path.dirname(self.__db_path))
            os.makedirs(os.path.dirname(self.__db_path))

        if self._connectdb(returniferror = True, cursor = False) is None:
            raise Exception("Cannot connect to database file %s" % self.__db_path)

        cur = self.__conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS packages(name text primary key, version text not null)")
        cur.execute("CREATE TABLE IF NOT EXISTS scripts(package text not null, type text not null, script text not null)")
        cur.execute("""CREATE TABLE IF NOT EXISTS
		files(package text not null,
			path text primary key,
			kind text not null,
			checksum text,
			uid integer,
			gid integer,
			flags integer,
			mode integer)""")
        self._closedb()
        return

    def _connectdb(self, returniferror = False, cursor = False):
	import sqlite3
        if self.__conn is not None:
            if cursor:
                return self.__conn.cursor()
            return True
        try:
            conn = sqlite3.connect(self.__db_path)
        except Exception as err:
            log.error(
                "%s:  Cannot connect to database %s: %s",
                sys.argv[0],
                self.__db_path,
                str(err),
            )
            if returniferror: return None
            raise err

        conn.text_factory = str
        conn.row_factory = sqlite3.Row
        self.__conn = conn
        if cursor:
            return self.__conn.cursor()
        return True

    def _closedb(self):
        if self.__conn is not None:
            self.__conn.commit()
            self.__conn.close()
            self.__conn = None
        return

    def FindPackage(self, pkgName):
        self._connectdb()
        cur = self.__conn.cursor()
        cur.execute("SELECT name, version FROM packages WHERE name = ?", (pkgName, ))
        rv = cur.fetchone()
        self._closedb()
        if rv is None: return None
        return { rv["name"] : rv["version"] }

    def UpdatePackage(self, pkgName, curVers, newVers, scripts):
        cur = self.FindPackage(pkgName)
        if cur is None:
            raise Exception("Package %s is not in system database, cannot update" % pkgName)
        if cur[pkgName] != curVers:
            raise Exception("Package %s is at version %s, not version %s as requested by update" % (cur[pkgName], curVers))

        if cur[pkgName] == newVers:
            log.warn(
                "Package %s version %s not changing, so not updating",
                pkgName,
                newVers,
            )
            return
        self._connectdb()
        cur = self.__conn.cursor()
        cur.execute("UPDATE packages SET version = ? WHERE name = ?", (newVers, pkgName))
        cur.execute("DELETE FROM scripts WHERE package = ?", (pkgName,))
        if scripts is not None:
            for scriptType in scripts.keys():
                cur.execute("INSERT INTO scripts(package, type, script) VALUES(?, ?, ?)",
                            (pkgName, scriptType, scripts[scriptType]))

        self._closedb()

    def AddPackage(self, pkgName, vers, scripts):
        curVers = self.FindPackage(pkgName)
        if curVers is not None:
            raise Exception("Package %s is already in system database, cannot add" % pkgName)
        self._connectdb()
        cur = self.__conn.cursor()
        cur.execute("INSERT INTO packages VALUES(?, ?)", (pkgName, vers))
        if scripts is not None:
            for scriptType in scripts.keys():
                cur.execute("INSERT INTO scripts(package, type, script) VALUES(?, ?, ?)",
                            (pkgName, scriptType, scripts[scriptType]))
        self._closedb()


    def FindScriptForPackage(self, pkgName, scriptType = None):
        cur = self._connectdb(cursor = True)
        if scriptType is None:
            cur.execute("SELECT type, script FROM scripts WHERE package = ?", (pkgName, ))
        else:
            cur.execute("SELECT type, script FROM scripts WHERE package = ? and type = ?",
                        (pkgName, scriptType))

        scripts = cur.fetchall()
        self._closedb()
        rv = {}
        for s in scripts:
            rv[s["type"]] = s["script"]

        return rv

    def FindFilesForPackage(self, pkgName = None):
        self._connectdb()
        cur = self.__conn.cursor()
        if pkgName is None:
            cur.execute("SELECT path, package, kind, checksum, uid, gid, flags, mode FROM files")
        else:
            cur.execute("SELECT path, package, kind, checksum, uid, gid, flags, mode FROM files WHERE package = ?", (pkgName,))

        files = cur.fetchall()
        self._closedb()
        rv = []
        for f in files:
            tmp = {}
            for k in f.keys():
                tmp[k] = f[k]
            rv.append(tmp)
        return rv

    def FindFile(self, path):
        self._connectdb()
        cur = self.__conn.cursor()
        cur.execute("SELECT * FROM files WHERE path = ?", (path,))
        row = cur.fetchone()
        self._closedb()
        if row is None:
            return None
        rv = {}
        for k in row.keys():
            rv[k] = row[k]
        return rv

    def AddFilesBulk(self, list):
        self._connectdb()
        cur = self.__conn.cursor()
        stmt = "INSERT OR REPLACE INTO files(package, path, kind, checksum, uid, gid, flags, mode) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        cur.executemany(stmt, list)
        self._closedb()

    def AddFile(self, pkgName, path, type, checksum = "", uid = 0, gid = 0, flags = 0, mode = 0):
        update = False
        if self.FindFile(path) is not None:
            update = True
        self._connectdb()
        cur = self.__conn.cursor()
        if update:
            stmt = "UPDATE files SET package = ?, kind = ?, path = ?, checksum = ?, uid = ?, gid = ?, flags = ?, mode = ? WHERE path = ?"
            args = (pkgName, type, path, checksum, uid, gid, flags, mode, path)
        else:
            stmt = "INSERT INTO files(package, kind, path, checksum, uid, gid, flags, mode) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
            args = (pkgName, type, path, checksum, uid, gid, flags, mode)
        cur.execute(stmt, args)
        self._closedb()

    def RemoveFileEntry(self, path):
        if self.FindFile(path) is not None:
            self._connectdb()
            cur = self.__conn.cursor()
            cur.execute("DELETE FROM files WHERE path = ?", (path, ))
            self._closedb()
        return

    def RemovePackageFiles(self, pkgName):
        # Remove the files in a package.  This removes them from
        # both the filesystem and database.
        if self.FindPackage(pkgName) is None:
            log.warn("Package %s is not in database", pkgName)
            return False

        self._connectdb()
        cur = self.__conn.cursor()

        cur.execute("SELECT path FROM files WHERE package = ? AND kind <> ?", (pkgName, "dir"))
        rows = cur.fetchall()
        file_list = []
        for row in rows:
            path = row[0]
            full_path = self.__db_root + "/" +  path
            if Installer.RemoveFile(full_path) == False:
                raise Exception("Cannot remove file %s" % path)
            file_list.append((path, ))
        cur.executemany("DELETE FROM files WHERE path = ?", file_list)
        cur.execute("VACUUM")
        self._closedb()
        return True

    def RemovePackageDirectories(self, pkgName, failDirectoryRemoval = False):
        # Remove the directories in a package.  This removes them from
        # both the filesystem and database.  If failDirectoryRemoval is True,
        # and a directory cannot be removed, return False.  Otherwise,
        # ignore that.

        if self.FindPackage(pkgName) is None:
            log.warn("Package %s is not in database", pkgName)
            return False

        self._connectdb()
        cur = self.__conn.cursor()

        dir_list = []
        cur.execute("SELECT path FROM files WHERE package = ? AND kind = ?", (pkgName, "dir"))
        rows = cur.fetchall()
        for row in rows:
            path = row[0]
            full_path = self.__db_root + "/" + path
            if Installer.RemoveDirectory(full_path) == False and failDirectoryRemoval == True:
                raise Exception("Cannot remove directory %s" % path)
            dir_list.append((path, ))
        cur.executemany("DELETE FROM files WHERE path = ?", dir_list)
        cur.execute("VACUUM")
        self._closedb()
        return True

    def RemovePackageScripts(self, pkgName):
        if self.FindPackage(pkgName) is None:
            log.warn(
                "Package %s is not in database, cannot remove scripts",
                pkgName,
            )
            return False

        cur = self._connectdb(cursor = True)
        cur.execute("DELETE FROM scripts WHERE package = ?", (pkgName, ))
        self._closedb()
        return True

    # This removes the contents of the given packages from both the filesystem
    # and the database.  It leaves the package itself in the database.
    def RemovePackageContents(self, pkgName, failDirectoryRemoval = False):
        if self.FindPackage(pkgName) is None:
            log.warn("Package %s is not in database", pkgName)
            return False

        if self.RemovePackageFiles(pkgName) == False:
            return False
        if self.RemovePackageDirectories(pkgName, failDirectoryRemoval) == False:
            return False
        if self.RemovePackageScripts(pkgName) == False:
            return False

        return True

    # Note that this just affects the database, it doesn't run any script.
    # That makes it the opposite of RemovePackageContents().
    def RemovePackage(self, pkgName):
        if self.FindPackage(pkgName) is not None:
            flist = self.FindFilesForPackage(pkgName)
            if len(flist) != 0:
                log.error(
                    "Can't remove package %s, it has %d files still",
                    pkgName,
                    len(flist),
                )
                raise Exception("Cannot remove package %s if it still has files" % pkgName)
            dlist = self.FindScriptForPackage(pkgName)
            if dlist is not None and len(dlist) != 0:
                log.error(
                    "Cannot remove package %s, it still has scripts",
                    pkgName,
                )
                raise Exception("Cannot remove package %s as it still has scripts" % pkgName)

        self._connectdb()
        cur = self.__conn.cursor()
        cur.execute("DELETE FROM packages WHERE name = ?", (pkgName, ))
        self._closedb()
        return

class UpdateServer(object):
    def __init__(self, name = None, url = None, master = None, signing = True):
        if name is None:
            raise ValueError("Cannot initialize UpdateServer with no name")
        else:
            self._name = name
        if url is None:
            raise ValueError("Cannot initialize UpdateServer with no URL")
        else:
            self._url = url
        self._master = master
        self._signature_required = signing

    @property
    def master(self):
        if self._master:
            return self._master
        else:
            return self.url

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        if name is None:
            raise ValueError("Cannot set UpdateServer name to nothing")
        self._name = name
    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, url):
        if url is None:
            raise ValueError("Cannot set UpdateServer URL to nothing!")
        self._url = url
    @property
    def signature_required(self):
        return self._signature_required
    @signature_required.setter
    def signature_required(self, sr):
        self._signature_required = sr

default_update_server = UpdateServer(name = "default",
                                     url = UPDATE_SERVER,
                                     master = MASTER_UPDATE_SERVER,
                                     signing = True)

class Configuration(object):
    _root = ""
    _config_path = "/data/update.conf"
    _temp = "/tmp"
    _system_dataset = "/var/db/system"
    _package_dir = None

    def __init__(self, root = None, file = None):
        if root is not None: self._root = root
        if file is not None: self._config_path = file
        self._update_server = default_update_server
        self.LoadConfigurationFile(self._config_path)
        # Set _temp to the system pool, if it exists.
        if os.path.exists(self._system_dataset):
            self._temp = self._system_dataset

    def UpdateServerMaster(self):
        return self._update_server.master
    def UpdateServerURL(self):
        return self._update_server.url
    def UpdateServerName(self):
        return self._update_server.name
    def UpdateServerSigned(self):
        return self._update_server.signature_required

    def TryGetNetworkFile(self, file=None, url=None, handler=None, pathname = None, reason = None, intr_ok = False):
        from . import DEFAULT_CA_FILE

        AVATAR_VERSION = "X-%s-Manifest-Version" % Avatar()
        current_version = "unknown"
        host_id = None
        if file and url:
            log.debug("Cannot specify both file and url for TryGetNetworkFile")
            raise Exception("Bad use of TryGetNetworkFile")
        if (not file) and (not url):
            log.debug("Must specify at file xor url for TryGetNetworkFile")
            raise Exception("Bad use of TryGetNetworkFile again")

        if file:
            # If we're looking for a file in general, look in the update server and the master.
            file_url = ["%s/%s" % (self.UpdateServerURL(), file)]
            if self.UpdateServerURL() != self.UpdateServerMaster():
                file_url.append("%s/%s" % (self.UpdateServerMaster(), file))
        elif url:
            file_url = [url]
        log.debug("TryGetNetworkFile(%s)" % file_url)
        temp_mani = self.SystemManifest()
        if temp_mani:
            current_version = temp_mani.Sequence()
        try:
            host_id = open("/etc/hostid").read().rstrip()
        except:
            host_id = None

        license_data = None
        try:
            from freenasUI.support.utils import LICENSE_FILE
            if os.path.exists(LICENSE_FILE):
                license_data = open(LICENSE_FILE, "r").read().rstrip()
        except:
            pass

        read = 0
        retval = None
        if pathname:
            if intr_ok:
                try:
                    retval = open(pathname, "r+b")
                    read = os.fstat(retval.fileno()).st_size
                    retval.seek(read)
                except:
                    pass
            if retval is None:
                retval = open(pathname, "w+b")
        else:
            retval = tempfile.TemporaryFile(dir = self._temp)
            
        if read > 0:  log.debug("File already exists, using a starting size of %d" % read)

        furl = None
        for url in file_url:
            url_exc = None
            try:
                https_handler = VerifiedHTTPSHandler(ca_certs = DEFAULT_CA_FILE)
                opener = urllib2.build_opener(https_handler)
                req = urllib2.Request(url)
                req.add_header("X-iXSystems-Project", Avatar())
                req.add_header("X-iXSystems-Version", current_version)
                if host_id:
                    req.add_header("X-iXSystems-HostID", host_id)
                if reason:
                    req.add_header("X-iXSystems-Reason", reason)
                if license_data:
                    req.add_header("X-iXSystems-License", license_data)

                # Hack for debugging
                req.add_header("User-Agent", "%s=%s" % (AVATAR_VERSION, current_version))
                # Allow restarting
                if intr_ok:
                    req.add_header("Range", "bytes=%d-" % read)
            
                furl = opener.open(req, timeout=30)
            except urllib2.HTTPError as error:
                if error.code == httplib.REQUESTED_RANGE_NOT_SATISFIABLE:
                    # We've reached the end of the file already
                    # Can I get this incorrectly from any other server?
                    # Do I need to do something different for the progress handler?
                    retval.seek(0)
                    return retval
                log.error("Got http error %s" % str(error))
                url_exc = error
            except BaseException as e:
                log.error("Unable to load %s: %s", url, str(e))
                url_exc = e

            if furl:
                break
            
        # The loop above should leave url_exc set to None if the file was
        # grabbed.
        if url_exc:
            if furl:
                furl.close()
                furl = None
            if retval:
                retval.close()
            log.error("Unable to load %s: %s", file_url, str(url_exc))
            raise url_exc

        # This _shouldn't_ be doable, but I'm checking just in case.
        if furl is None:
            log.error("Unable to load %s", file_url)
            if retval:
                retval.close()
            return None
        
        try:
            totalsize = int(furl.info().getheader('Content-Length').strip())
        except:
            totalsize = None

        chunk_size = 64 * 1024
        mbyte = 1024 * 1024
        lastpercent = percent = 0
        lasttime = time.time()
        try:
            while True:
                data = furl.read(chunk_size)
                tmptime = time.time()
                if tmptime - lasttime > 0:
                    downrate = int(chunk_size / (tmptime - lasttime))
                else:
                    downrate = chunk_size
                lasttime = tmptime
                if not data:
                    log.debug("TryGetNetworkFile(%s):  Read %d bytes total" % (file_url, read))
                    break
                read += len(data)
                if ((read % mbyte) == 0):
                    log.debug("TryGetNetworkFile(%s):  Read %d bytes" % (file_url, read))

                if handler and totalsize:
                    percent = int((float(read) / float(totalsize)) * 100.0)
                    if percent != lastpercent:
                        handler(
                            'network',
                            url,
                            size=totalsize,
                            progress=percent,
                            download_rate=downrate,
                        )
                    lastpercent = percent
                retval.write(data)
        except Exception as e:
            log.debug("Got exception %s" % str(e))
            if intr_ok == False and pathname:
                os.unlink(pathname)
            raise e
        retval.seek(0)
        return retval

    # Load the list of currently-watched trains.
    # The file is a JSON file.
    # This sets self._trains as a dictionary of
    # Train objects (key being the train name).
    def LoadTrainsConfig(self, updatecheck = False):
        import json
        self._trains = {}
        if self._temp:
            train_path = self._temp + "/Trains.json"
            try:
                with open(train_path, "r") as f:
                    trains = json.load(f)
                for train_name in trains.keys():
                    temp = Train.Train(train_name)
                    if TRAIN_DESC_KEY in trains[train_name]:
                        temp.SetDescription(trains[train_name][TRAIN_DESC_KEY])
                    if TRAIN_SEQ_KEY in trains[train_name]:
                        temp.SetLastSequence(trains[train_name][TRAIN_SEQ_KEY])
                    if TRAIN_CHECKED_KEY in trains[train_name]:
                        temp.SetLastCheckedTime(trains[train_name][TRAIN_CHECKED_KEY])
                    self._trains[train_name] = temp
            except:
                pass
        sys_mani = self.SystemManifest()
        if sys_mani.Train() not in self._trains:
            temp = Train.Train(sys_mani.Train(), "Installed OS", sys_mani.Sequence())
            self._trains[temp.Name()] = temp
        if updatecheck:
            for train in self._trains:
                new_man = self.FindLatestManifest(train.Name())
                if new_man:
                    if new_man.Sequence() != train.LastSequence():
                        # We have an update
                        train.SetLastSequence(new_man.Sequence())
                        train.SetLastCheckedTime()
                        train.SetNotes(new_man.Notes())
                        train.SetNotice(new_man.Notice())
                        train.SetUpdate(True)
        return

    # Save the list of currently-watched trains.
    def SaveTrainsConfig(self):
        import json
        sys_mani = self.SystemManifest()
        current_train = sys_mani.Train()
        if self._trains is None: self._trains = {}
        if current_train not in self._trains:
            self._trains[current_train] = Train.Train(current_train, "Installed OS", sys_mani.Sequence())
        if self._temp:
            obj = {}
            for train_name in self._trains.keys():
                train = self._trains[train_name]
                temp = {}
                if train.Description():
                    temp[TRAIN_DESC_KEY] = train.Description()
                if train.LastSequence():
                    temp[TRAIN_SEQ_KEY] = train.LastSequence()
                if train.LastCheckedTime():
                    temp[TRAIN_CHECKED_KEY] = train.LastCheckedTime()
                obj[train_name] = temp
            train_path = self._temp + "/Trains.json"
            try:
                with open(train_path, "w") as f:
                    json.dump(obj, f, sort_keys=True,
                              indent=4, separators=(',', ': '))
            except OSError as e:
                log.error("Could not write out trains:  %s" % str(e))
        return

    def SystemManifest(self):
        man = Manifest.Manifest(configuration = self)
        try:
            man.LoadPath(self._root + Manifest.SYSTEM_MANIFEST_FILE)
        except:
            man = None
        return man

    def PackageDB(self, root = None, create = True):
        if root is None: root = self._root
        return PackageDB(root, create)

    def LoadConfigurationFile(self, path):
        cfp = None
        try:
            with open(self._root + path, "r") as f:
                cfp = ConfigParser.SafeConfigParser()
                cfp.readfp(f)
        except:
            return

        if cfp is None:
            return

        upd = None
        for section in cfp.sections():
            if section == CONFIG_DEFAULT:
                if cfp.has_option(CONFIG_DEFAULT, CONFIG_SERVER):
                    upd = cfp.get(CONFIG_DEFAULT, CONFIG_SERVER)
            else:
                if cfp.has_option(section, UPDATE_SERVER_NAME_KEY) and \
                   cfp.has_option(section, UPDATE_SERVER_URL_KEY) and \
                   section == upd:
                    # This is an update server section
                    n = cfp.get(section, UPDATE_SERVER_NAME_KEY)
                    u = cfp.get(section, UPDATE_SERVER_URL_KEY)
                    s = cfp.getboolean(section, UPDATE_SERVER_SIGNED_KEY) \
                        if cfp.has_option(section, UPDATE_SERVER_SIGNED_KEY) else True
                    m = cfp.get(section, UPDATE_SERVER_MASTER_KEY) \
                        if cfp.has_option(section, UPDATE_SERVER_MASTER_KEY) else None
                    try:
                        update_server = UpdateServer(name = n, url = u, signing = s, master = m)
                        self._update_server = update_server
                    except:
                        log.error("Cannot set update server to %s, using default", n)
        # End for loop here
        return

    def SetPackageDir(self, loc):
        self._package_dir = loc
        return

    def AddSearchLocation(self, loc, insert = False):
        raise Exception("Deprecated method")
        if self._search is None:  self._search = []
        if insert is True:
            self._search.insert(0, loc)
        else:
            self._search.append(loc)
        return

    def SetSearchLocations(self, list):
        raise Exception("Deprecated method")
        self._search = list
        return
    
    def SearchLocations(self):
        return SEARCH_LOCATIONS

    def AddTrain(self, train):
        self._trains.append(train)
        return

    def CurrentTrain(self):
        """
        Returns the name of the train of the current
        system.  It may return None, but that's for edge cases
        generally related to installation and build environments.
        """
        sys_mani = self.SystemManifest()
        if sys_mani:
            if sys_mani.NewTrain():
                return sys_mani.NewTrain()
            return sys_mani.Train()
        return None

    def AvailableTrains(self):
        """
        Returns the set of available trains from
        the upgrade server.  The return value is
        a dictionary, keyed by the train name, and
        value being the description.
        The list of trains is on the upgrade server,
        with the name "trains.txt".  Or whatever
        I decide it should be called.
        """
        rv = {}
        fileref = self.TryGetNetworkFile(file = TRAIN_FILE, reason = "FetchTrains")

        if fileref is None:
            return None

        for line in fileref:
            import re
            line = line.rstrip()
            # Ignore comments
            if line.startswith("#"):
                continue
            # Input is <name><white_space><description>
            m = re.search("(\S+)\s+(.*)$", line)
            if m is None or m.lastindex == None:
                log.debug("Input line `%s' is unparsable" % line)
                continue
            rv[m.group(1)] = m.group(2)

        return rv if len(rv) > 0 else None

    def WatchedTrains(self):
        if self._trains is None:
            self._trains = self.LoadTrainsConfig()
        return self._trains

    def WatchTrain(self, train, watch = True):
        """
        Add a train to the local set to be watched.
        A watched train is checked for updates.
        If the train is already watched, this does nothing.
        train is a Train object.
        If stop is True, then this is used to stop watching
        this particular train.
        """
        if self._trains is None:
            self._trains = {}
        if watch:
            if train.Name() not in self._trains:
                self._trains[train.Name()] = train
        else:
            if train.Name() in self._trains:
                self._trains.pop(train.Name())
        return

    def SetTrains(self, tlist):
        self._trains = tlist
        return

    def TemporaryDirectory(self):
        return self._temp

    def SetTemporaryDirectory(self, path):
        if path:
            self._temp = path
        return

    def CreateTemporaryFile(self):
        return tempfile.TemporaryFile(dir = self._temp)

    def PackagePath(self, pkg):
        if self._package_dir:
            return "%s/%s" % (self._package_dir, pkg.FileName())
        else:
            return "%s/Packages/%s" % (self.UpdateServerURL(), pkg.FileName())

    def PackageUpdatePath(self, pkg, old_version):
        # Do we need this?  If we're given a package directory,
        # then we won't have updates.
        if self._package_dir:
            return "%s/%s" % (self._package_dir, pkg.FileName(old_version))
        else:
            return "%s/Packages/%s" % (self.UpdateServerURL(), pkg.FileName(old_version))

    def GetManifest(self, train = None, sequence = None, handler = None):
        """
        GetManifest:  fetch, over the network, the requested
        manifest file.  If train isn't specified, it'll use
        the current system; if sequence isn't specified, it'll
        use LATEST.
        Returns either a manifest object, or None.
        """
        # Get the specified manifeset.
        # If train is None, then we use the current train;
        # if sequence is None, then we get LATEST.
        sys_mani = self.SystemManifest()
        if sys_mani is None:
            raise Exceptions.ConfigurationInvalidException
        if train is None:
            train = sys_mani.Train()
        if sequence is None:
            ManifestFile = "/%s/LATEST" % train
        else:
            # This needs to change for TrueNAS, doesn't it?
            ManifestFile = "%s/%s-%s" % (Avatar(), train, sequence)

        file_ref = self.TryGetNetworkFile(url = "%s/%s" % (self.UpdateServerMaster(), ManifestFile),
                                          handler=handler,
                                          reason = "GetManifest",
                                 )
        return file_ref

    def FindLatestManifest(self, train = None, require_signature = False):
        # Gets <UPDATE_SERVER>/<train>/LATEST
        # Returns a manifest, or None.
        rv = None
        temp_mani = self.SystemManifest()

        if train is None:
            if temp_mani is None:
                # I give up
                raise Exceptions.ConfigurationInvalidException
            if temp_mani.NewTrain():
                # If we're redirected to a new train, use that.
                train = temp_mani.NewTrain()
            else:
                train = temp_mani.Train()

        file = self.TryGetNetworkFile(url = "%s/%s/LATEST" % (self.UpdateServerMaster(), train),
                                      reason = "GetLatestManifest",
                                  )
        if file is None:
            log.debug("Could not get latest manifest file for train %s" % train)
        else:
            rv = Manifest.Manifest(self, require_signature = require_signature)
            rv.LoadFile(file)
        return rv

    def CurrentPackageVersion(self, pkgName):
        try:
            pkgdb = self.PackageDB(create = False)
            if pkgdb:
                pkgInfo = pkgdb.FindPackage(pkgName)
                if pkgInfo:
                    return pkgInfo[pkgName]
        except:
            pass
        return None

    def GetChangeLog(self, train, save_dir = None, handler = None):
        # Look for the changelog file for the specific train, and attempt to
        # download it.  If save_dir is set, save it as save_dir/ChangeLog.txt
        # Returns a file for the ChangeLog, or None if it can't be found.
        changelog_url = "%s/ChangeLog.txt" % train
        if save_dir:
            save_path = "%s/ChangeLog.txt" % save_dir
        else:
            save_path = None
        try:
            file = self.TryGetNetworkFile(
                file = changelog_url,
                handler = handler,
                pathname = save_path,
                reason = "GetChangeLog",
            )
            return file
        except:
            log.debug("Could not get ChangeLog.txt, ignoring")
            return None
    
    def FindPackageFile(self, package, upgrade_from=None, handler=None, save_dir = None, pkg_type = None):
        from Update import PkgFileDeltaOnly, PkgFileFullOnly
        # Given a package, and optionally a version to upgrade from, find
        # the package file for it.  Returns a file-like
        # object for the package file.
        # If the package object has a checksum set, it
        # attempts to verify the checksum; if it doesn't match,
        # it goes onto the next one.
        # If upgrade_from is set, it tries to find delta packages
        # first, and will verify the checksum for that.  If the
        # package does not have an upgrade field set, or it does
        # but there's no checksum, then we are probably creating
        # the manifest file, so we won't do the checksum verification --
        # we'll only go by name.
        # If it can't find one, it returns None

        # We have at least one, and at most two, files
        # to look for.
        # The first file is the full package.
        package_files = []
        if pkg_type is not PkgFileDeltaOnly:
            package_files.append({ "Filename" : package.FileName(), "Checksum" : package.Checksum()})
        # The next one is the delta package, if it exists.
        # For that, we look through package.Updates(), looking for one that
        # has the same version as what is currently installed.
        # So first we have to get the current version.
        if pkg_type is not PkgFileFullOnly:
            try:
                pkgdb = self.PackageDB(create = False)
                if pkgdb:
                    pkgInfo = pkgdb.FindPackage(package.Name())
                    if pkgInfo:
                        curVers = pkgInfo[package.Name()]
                        if curVers and curVers != package.Version():
                            upgrade = package.Update(curVers)
                            if upgrade:
                                tdict = { "Filename" : package.FileName(curVers),
                                          "Checksum" : None,
                                          "Reboot"   : upgrade.RequiresReboot(),
                                          "Delta"    : True,
                                      }
                                if upgrade.Checksum():
                                    tdict[Package.CHECKSUM_KEY] = upgrade.Checksum()
                                if upgrade.Size():
                                    tdict[Package.SIZE_KEY] = upgrade.Size()    
                                package_files.append(tdict)
            except:
                # No update packge that matches.
                pass

        # At this point, package_files now has at least one element.
        # We want to search in this order:
        # * Local full copy
        # * Local delta copy
        # * Network delta copy
        # * Network full copy

        # We want to look for each one in _package_dir and off the network.
        # If we find it, and the checksum matches, we're good to go.
        # If not, we have to grab it off the network and use that.  We can't
        # check that checksum until we get it.
        for search_attempt in package_files:
            # First try the local copy.
            log.debug("Searching for %s" % search_attempt["Filename"])
            try:
                if self._package_dir:
                    p = "%s/%s" % (self._package_dir, search_attempt["Filename"])
                    if os.path.exists(p):
                        file = open(p)
                        log.debug("Found package file %s" % p)
                        if search_attempt["Checksum"]:
                            h = ChecksumFile(file)
                            if h == search_attempt["Checksum"]:
                                return file
                        else:
                            # No checksum for the file, so we'll just go with it.
                            return file
            except:
                pass

        for search_attempt in reversed(package_files):
            # Next we try to get it from the network.
            pFile = "Packages/%s" % search_attempt["Filename"]
            save_name = None
            if save_dir:
                save_name = save_dir + "/" + search_attempt["Filename"]

            file = self.TryGetNetworkFile(
                file = pFile,
                handler = handler,
                pathname = save_name,
                reason = "DownloadPackageFile",
                intr_ok = True
                )
            if file:
                if search_attempt["Checksum"]:
                    h = ChecksumFile(file)
                    if h == search_attempt["Checksum"]:
                        return file
                    else:
                        # For an interrupted download of a package file,
                        # this won't be reached due to an exception.
                        log.debug("Checksum doesn't match, removing file")
                        if save_name: os.unlink(save_name)
                else:
                    # No checksum for the file, so we just go with it
                    return file

        return None

def is_ignore_path(path):
    for i in VERIFY_SKIP_PATHS:
        tlen = len(i)
        if path[:tlen] == i:
            return True
    return False

def get_ftype_and_perm(mode):
    """ Returns a tuple of whether the file is: file(regular file)/dir/slink
    /char. spec/block spec/pipe/socket and the permission bits of the file.
    If it does not match any of the cases below (it will return "unknown" twice)"""
    if S_ISREG(mode):
        return "file", S_IMODE(mode)
    if S_ISDIR(mode):
        return "dir", S_IMODE(mode)
    if S_ISLNK(mode):
        return "slink", S_IMODE(mode)
    if S_ISCHR(mode):
        return "character special", S_IMODE(mode)
    if S_ISBLK(mode):
        return "block special", S_IMODE(mode)
    if S_ISFIFO(mode):
        return "pipe", S_IMODE(mode)
    if S_ISSOCK(mode):
        return "socket", S_IMODE(mode)
    return "unknown", "unknown"

def check_ftype(objs):
    """ Checks the filetype, permissions and uid,gid of the
    pkgdg object(objs) sent to it. Returns two dicts: ed and pd
    (the error_dict with a descriptive explanantion of the problem
    if present, none otherwise, the perm_dict with a description of
    the incoorect perms if present, none otherwise
    """
    ed = None
    pd = None
    lst_var = os.lstat(objs["path"])
    ftype, perm = get_ftype_and_perm(lst_var.st_mode)
    if ftype != objs["kind"]:
        ed = dict([('path', objs["path"]),
                ('problem', 'Expected %s, Got %s' %(objs["kind"], ftype)),
                ('pkgdb_entry', objs)])
    pdtmp = ''
    if perm!=objs["mode"]:
        pdtmp+="\nExpected MODE: %s, Got: %s" %(oct(objs["mode"]), oct(perm))
    if lst_var.st_uid!=objs["uid"]:
        pdtmp+="\nExpected UID: %s, Got: %s" %(objs["uid"], lst_var.st_uid)
    if lst_var.st_gid!=objs["gid"]:
        pdtmp+="\nExpected GID: %s, Got: %s" %(objs["gid"], lst_var.st_gid)
    if pdtmp and not objs["path"].endswith(".pyc"):
        pd = dict([('path', objs["path"]),
                ('problem', pdtmp[1:]),
                ('pkgdb_entry', objs)])
    return ed, pd

def do_verify(verify_handler=None):
    """A function that goes through the provided pkgdb filelist and verifies it with
    the current root filesystem."""
    error_flag = False
    error_list = dict([('checksum', []), ('wrongtype',[]), ('notfound',[])])
    warn_flag = False
    warn_list = []
    i=0 # counter for progress indication in the UI

    pkgdb = PackageDB(create = False)
    if pkgdb is None:
        raise IOError("Cannot get pkgdb connection")
    filelist = pkgdb.FindFilesForPackage()
    total_files  = len(filelist)

    for objs in filelist:
        i = i+1
        if verify_handler is not None:
            verify_handler(i,total_files,objs["path"])
        tmp = '' # Just a temp. variable to store the text to be hashed
        if is_ignore_path(objs["path"]):
            continue
        if not os.path.lexists(objs["path"]):
            # This basically just checks if the file/slink/dir exists or not.
            # Note: not using os.path.exists(path) here as that returns false
            # even if its a broken symlink and that is a differret problem
            # and will be caught in one of the if conds below.
            # For more information: https://docs.python.org/2/library/os.path.html
            error_flag = True
            error_list['notfound'].append(dict([('path', objs["path"]),
                ('problem', 'path does not exsist'),
                ('pkgdb_entry', objs)]))
            continue

        ed, pd = check_ftype(objs)
        if ed:
            error_flag = True
            error_list['wrongtype'].append(ed)
        if pd:
            warn_flag = True
            warn_list.append(pd)

        if objs["kind"] == "slink":
            tmp = os.readlink(objs["path"])
            if tmp.startswith('/'):
                tmp = tmp[1:]

        if objs["kind"] == "file":
            if objs["path"].endswith(".pyc"):
                continue
            tmp = open(objs["path"]).read()

        # Do this last (as it needs to be done for all, but dirs, as dirs have no checksum d'oh!)
        if (
            objs["kind"] != 'dir' and
            objs["checksum"] and
            objs["checksum"] !="-" and
            hashlib.sha256(tmp).hexdigest()!=objs["checksum"]
        ):
            error_flag = True
            error_list['checksum'].append(dict([('path', objs["path"]),
                ('problem', 'checksum does not match'),
                ('pkgdb_entry', objs)]))
    return error_flag, error_list, warn_flag, warn_list
