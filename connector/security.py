import base64,ctypes,json,os,secrets
from pathlib import Path
class ConnectorError(Exception):
 def __init__(self,message,status=None):super().__init__(message);self.status=status
def state_directory():
 if os.name=='nt':return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'CasaVerdeConnector'
 return Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'casa-verde-connector'
def protect(data):
 if os.name!='nt':return b'POSIX1:'+data
 from ctypes import wintypes
 class Blob(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]
 buffer=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
 crypt=ctypes.windll.crypt32;kernel=ctypes.windll.kernel32
 crypt.CryptProtectData.argtypes=[ctypes.POINTER(Blob),wintypes.LPCWSTR,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)];crypt.CryptProtectData.restype=wintypes.BOOL
 if not crypt.CryptProtectData(ctypes.byref(source),'Casa Verde',None,None,None,1,ctypes.byref(target)):raise ConnectorError('Não foi possível proteger credenciais com o Windows.')
 try:return b'DPAPI1:'+ctypes.string_at(target.pbData,target.cbData)
 finally:kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree(ctypes.cast(target.pbData,ctypes.c_void_p))
def unprotect(data):
 if os.name!='nt':
  if not data.startswith(b'POSIX1:'):raise ConnectorError('Arquivo de credenciais incompatível com este computador.')
  return data[7:]
 if not data.startswith(b'DPAPI1:'):raise ConnectorError('Arquivo de credenciais não protegido pelo Windows.')
 from ctypes import wintypes
 class Blob(ctypes.Structure):_fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]
 raw=data[7:];buffer=ctypes.create_string_buffer(raw);source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)));target=Blob()
 crypt=ctypes.windll.crypt32;kernel=ctypes.windll.kernel32
 crypt.CryptUnprotectData.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)];crypt.CryptUnprotectData.restype=wintypes.BOOL
 if not crypt.CryptUnprotectData(ctypes.byref(source),None,None,None,None,1,ctypes.byref(target)):raise ConnectorError('O Windows não conseguiu abrir estas credenciais. Use o mesmo usuário ou conecte novamente.')
 try:return ctypes.string_at(target.pbData,target.cbData)
 finally:kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree(ctypes.cast(target.pbData,ctypes.c_void_p))
class Store:
 def __init__(self,directory=None):
  self.directory=Path(directory) if directory else state_directory()
  if self.directory.is_symlink():raise ConnectorError('Diretório de credenciais inválido.')
  self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
  if os.name!='nt':self.directory.chmod(0o700)
  self.path=self.directory/'credentials.bin'
 def read(self):
  if not self.path.exists():return {'accounts':{},'active':None}
  if self.path.is_symlink():raise ConnectorError('Arquivo de credenciais inválido.')
  try:return json.loads(unprotect(self.path.read_bytes()))
  except ConnectorError:raise
  except Exception:raise ConnectorError('Arquivo local inválido. Não envie esse arquivo para suporte.') from None
 def write(self,data):
  if self.path.is_symlink():raise ConnectorError('Arquivo de credenciais inválido.')
  payload=protect(json.dumps(data,ensure_ascii=False).encode());temp=self.directory/('save-'+secrets.token_hex(8)+'.tmp')
  try:
   fd=os.open(str(temp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
   os.replace(temp,self.path)
   if os.name!='nt':self.path.chmod(0o600)
  finally:
   if temp.exists():temp.unlink()
