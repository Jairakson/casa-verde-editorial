"""Conexões PostgreSQL no Render; SQLite opcional apenas para execução local/testes."""
import sqlite3
from pathlib import Path
ROOT=Path(__file__).parent
class Row:
 def __init__(self,columns,values):self.columns=columns;self.values=values
 def __getitem__(self,key):return self.values[key] if isinstance(key,int) else self.values[self.columns.index(key)]
 def __iter__(self):return iter(self.values)
 def keys(self):return self.columns
class Cursor:
 def __init__(self,cursor):self.cursor=cursor
 @property
 def description(self):return self.cursor.description
 def wrap(self,row):return None if row is None else Row([c.name for c in self.cursor.description],row)
 def fetchone(self):return self.wrap(self.cursor.fetchone())
 def fetchall(self):return [self.wrap(row) for row in self.cursor.fetchall()]
 def __iter__(self):
  for row in self.cursor:yield self.wrap(row)
class Postgres:
 postgres=True
 def __init__(self,url):
  import psycopg
  self.connection=psycopg.connect(url,connect_timeout=10,options='-c statement_timeout=15000')
 def execute(self,sql,params=()):
  if sql=='BEGIN IMMEDIATE':sql='SELECT pg_advisory_xact_lock(68194321)'
  return Cursor(self.connection.execute(sql.replace('?','%s'),params or None))
 def commit(self):self.connection.commit()
 def rollback(self):self.connection.rollback()
 def close(self):self.connection.close()
 def __enter__(self):return self
 def __exit__(self,kind,value,tb):
  try:self.rollback() if kind else self.commit()
  finally:self.close()
def connect(location):
 if location.startswith(('postgres://','postgresql://')):return Postgres(location)
 d=sqlite3.connect(location);d.row_factory=sqlite3.Row;d.execute('PRAGMA foreign_keys=ON');return d
def migrate(d):
 if getattr(d,'postgres',False):
  d.execute('SELECT pg_advisory_xact_lock(68194321)')
  d.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)')
  if not d.execute('SELECT 1 FROM schema_migrations WHERE version=1').fetchone():
   for sql in (ROOT/'migrations/postgres/001_initial.sql').read_text().split(';'):
    if sql.strip():d.execute(sql)
   d.execute('INSERT INTO schema_migrations VALUES(1)')
  d.commit()
 elif d.execute('PRAGMA user_version').fetchone()[0]==0:d.executescript((ROOT/'migrations/001_initial.sql').read_text())
try:
 import psycopg
 INTEGRITY_ERRORS=(sqlite3.IntegrityError,psycopg.IntegrityError)
except ImportError:INTEGRITY_ERRORS=(sqlite3.IntegrityError,)
