import unittest,os,tempfile,subprocess,sys,time,urllib.request
from unittest.mock import patch
import app
class Render(unittest.TestCase):
 def test_bootstrap_once(self):
  with app.connect(':memory:') as d:
   app.migrate(d)
   with patch.dict(os.environ,{'ADMIN_EMAIL':'admin@example.com','ADMIN_PASSWORD':'strong-test-password'}):app.bootstrap_admin(d)
   original=d.execute('SELECT password FROM users').fetchone()[0]
   with patch.dict(os.environ,{'ADMIN_EMAIL':'other@example.com','ADMIN_PASSWORD':'different-password'}):app.bootstrap_admin(d)
   self.assertEqual(d.execute('SELECT count(*) FROM users').fetchone()[0],1)
   self.assertEqual(d.execute('SELECT password FROM users').fetchone()[0],original)
 def test_weak_bootstrap_rejected(self):
  with app.connect(':memory:') as d:
   app.migrate(d)
   with patch.dict(os.environ,{'ADMIN_EMAIL':'admin@example.com','ADMIN_PASSWORD':'short'}):
    with self.assertRaises(ValueError):app.bootstrap_admin(d)
 def test_port_health_and_shutdown(self):
  import socket
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  with tempfile.TemporaryDirectory() as tmp:
   env=dict(os.environ,DATABASE_PATH=tmp+'/app.db',PORT=str(port),HOST='127.0.0.1',ADMIN_EMAIL='admin@example.com',ADMIN_PASSWORD='test-password-long')
   proc=subprocess.Popen([sys.executable,'app.py','serve'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   try:
    for i in range(50):
     try:
      with urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz',timeout=1) as res:self.assertEqual(res.read(),b'ok')
      break
     except OSError:time.sleep(.05)
    else:self.fail('Servidor não iniciou')
    proc.terminate();self.assertEqual(proc.wait(timeout=5),0)
   finally:
    if proc.poll() is None:proc.kill();proc.wait()
