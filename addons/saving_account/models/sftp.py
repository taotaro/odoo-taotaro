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
          port=rec.sftp_port,
          cnopts=cnopt,
        ) as sftp:
          sftp.cwd(rec.sftp_path)
      except Exception as e:
        raise Warning('There was a problem connecting to the remote ftp: ' + str(e))

      message_id = self.env['message.wizard'].create({'message': 'Connection success!'})
      return {
          'name': 'Success',
          'type': 'ir.actions.act_window',
          'view_mode': 'form',
          'res_model': 'message.wizard',
          'res_id': message_id.id,
          'target': 'new'
      }
