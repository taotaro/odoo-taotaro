from email.policy import default
from odoo import models, fields, api
import pysftp

class FileTransfer(models.Model):
  _name = "sftp"
  _description = "File Transfer Protocol"

  sftp_host = fields.Char(string="Host", required=True)
  sftp_path = fields.Char(string="Directory Path", required=True, default="/")
  sftp_user = fields.Char(string="Username", required=True)
  sftp_password = fields.Char(string="Password", required=True)
  sftp_port = fields.Integer(string="Port", required=True, default=22)
  sftp_hostkeys = fields.Char(string="Hostkeys")

  def sftp_test_connection(self):
    self.ensure_one()
    for rec in self:
      cnopt = pysftp.CnOpts()
      if rec.sftp_hostkeys:
        cnopt.hostkeys.load(rec.sftp_hostkeys)
      else:
        cnopt.hostkeys = None

      try:
        with pysftp.Connection(
          host=rec.sftp_host, 
          username=rec.sftp_user, 
          password=rec.sftp_password, 
          cnopts=cnopt,
          port=rec.sftp_port,
        ) as sftp:
          sftp.cwd(rec.sftp_path)
      except Exception as e:
        raise Warning('There was a problem connecting to the remote ftp: ' + str(e))
      raise Warning("Connection Success!!!")
