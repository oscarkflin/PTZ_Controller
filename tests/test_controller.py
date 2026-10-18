import socket
import struct
import threading
import unittest
import urllib.request
import urllib.error
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from server import Controller, command, make_handler, validate_config


class Tests(unittest.TestCase):
    def test_live_gate_and_transition(self):
        c = Controller()
        self.assertFalse(c.live)
        with patch.object(c,'send') as send:
            c.execute({'action':'recall','preset':0})
            c.execute({'action':'stop'})
            send.assert_not_called()
        c.config['mode']='visca-udp'
        with patch.object(c,'check_connection') as check, patch.object(c,'reset_sequence') as reset:
            c.connection_status='unreachable'
            c.set_live(True)
            self.assertTrue(c.live)
            check.assert_not_called()
        with patch.object(c,'send') as send:
            c.set_live(False)
            self.assertEqual(send.call_count,2)
            c.execute({'action':'zoom-step','direction':1})
            self.assertEqual(send.call_count,2)
            self.assertFalse(c.live)

    def test_pan_release_and_emergency_stop(self):
        c=Controller()
        c.live=True
        with patch.object(c,'send') as send:
            c.execute({'action':'move','x':1,'y':1,'speed':3,'client':'pan','order':1})
            c.execute({'action':'stop','client':'pan','order':3})
            self.assertEqual(send.call_args_list[1].args[0].hex(),'8101060101010303ff')
            self.assertEqual(send.call_args_list[2].args[0].hex(),'8101040700ff')
            c.execute({'action':'move','x':1,'y':1,'speed':3,'client':'pan','order':2})
            self.assertEqual(send.call_count,3)
            c.check_timeout()
            self.assertEqual(send.call_args.args[0].hex(),'8101060101010303ff')
            self.assertFalse(c.moving)
        with patch.object(c,'send',side_effect=[OSError('network'),None]) as send:
            with self.assertRaises(OSError): c.stop()
            self.assertEqual(send.call_count,2)

    def test_live_enable_resets_sony_without_waiting_for_reply(self):
        c=Controller()
        c.config=dict(mode='visca-udp',host='192.168.4.37',port=52381,framing='sony')
        c.sequence=500
        with patch('server.socket.socket') as factory:
            sock=factory.return_value.__enter__.return_value
            c.set_live(True)
            self.assertTrue(c.live)
            self.assertEqual(c.sequence,0)
            sock.sendto.assert_called_once_with(bytes.fromhex('02 00 00 01 00 00 00 00 01'),('192.168.4.37',52381))
            sock.recvfrom.assert_not_called()
            c.execute({'action':'zoom','direction':1,'speed':3})
            self.assertEqual(c.sequence,1)
            self.assertEqual(sock.sendto.call_args.args[0][:8],struct.pack('!HHI',0x100,6,1))

    def test_connection_inquiry_success_and_timeout(self):
        c = Controller()
        c.live = True
        c.config = dict(mode='visca-udp',host='192.168.4.37',port=52381,framing='sony')
        reply = bytes.fromhex('90 50 00 00 00 00 00 00 00 00 ff')
        with patch('server.socket.socket') as factory:
            sock = factory.return_value.__enter__.return_value
            sock.recvfrom.side_effect = [(bytes.fromhex('02 01 00 01 00 00 00 00 01'),('192.168.4.37',52381)),(struct.pack('!HHI',0x0111,len(reply),1)+reply,('192.168.4.37',52381))]
            c.check_connection()
            self.assertEqual(c.connection_status,'responding')
            self.assertEqual(sock.sendto.call_count,2)
            sock.recvfrom.side_effect = TimeoutError()
            c.check_connection()
            self.assertEqual(c.connection_status,'unreachable')

    def test_zoom_step_is_absolute_and_bounded(self):
        c = Controller()
        c.live = True
        c.config['mode']='visca-udp'
        with patch.object(c,'inquire',return_value=bytes.fromhex('90 50 03 0f 00 00 ff')), patch.object(c,'send') as send:
            c.execute({'action':'zoom-step','direction':1})
            send.assert_called_once_with(bytes.fromhex('81 01 04 47 04 00 00 00 ff'),confirm=True)
        with patch.object(c,'inquire',return_value=bytes.fromhex('90 50 00 00 01 00 ff')), patch.object(c,'send') as send:
            c.execute({'action':'zoom-step','direction':-1})
            send.assert_called_once_with(bytes.fromhex('81 01 04 47 00 00 00 00 ff'),confirm=True)

    def test_release_supersedes_delayed_zoom_without_ack(self):
        c=Controller()
        c.live=True
        with patch.object(c,'send') as send:
            c.execute({'action':'zoom','direction':1,'speed':3,'client':'browser','order':1})
            c.execute({'action':'stop','client':'browser','order':3})
            self.assertEqual(send.call_args_list[1].args[0].hex(),'8101040700ff')
            count=send.call_count
            c.execute({'action':'zoom','direction':1,'speed':3,'client':'browser','order':2})
            self.assertEqual(send.call_count,count)
            self.assertFalse(c.moving)
            c.check_timeout()
            self.assertEqual(send.call_count,count+1)
            c.execute({'action':'zoom','direction':-1,'speed':3,'client':'browser','order':4})
            count=send.call_count
            c.check_timeout()
            self.assertEqual(send.call_count,count)
            self.assertEqual(c.stop_retry_until,0)
            for call in send.call_args_list:
                self.assertNotIn('confirm',call.kwargs)

    def test_preset_names_persist_without_camera_commands(self):
        with tempfile.TemporaryDirectory() as tmp, patch('server.PRESETS', Path(tmp)/'names.json'):
            c = Controller()
            c.live = True
            with patch.object(c,'send') as send:
                c.rename_preset({'preset':0,'name':'  Wide shot  '})
                send.assert_not_called()
            self.assertEqual(Controller().preset_names['0'],'Wide shot')
            with self.assertRaises(ValueError): c.rename_preset({'preset':0,'name':'x'*41})

    def test_watchdog(self):
        c = Controller()
        c.live = True
        with patch.object(c,'send') as send:
            c.execute(dict(action='move',x=1,y=0,speed=3))
            c.last_motion -= 1
            c.check_timeout()
            self.assertFalse(c.moving)
            self.assertEqual(send.call_count,3)
            self.assertEqual(send.call_args_list[1].args[0].hex(),'8101060101010303ff')

    def test_udp_packet_without_network(self):
        c = Controller()
        c.live = True
        c.config = dict(mode='visca-udp',host='192.168.1.100',port=52381,framing='sony')
        with patch('server.socket.socket') as sock:
            c.send(bytes.fromhex('81010604ff'))
            sock.return_value.__enter__.return_value.sendto.assert_called_once_with(
                struct.pack('!HHI',0x100,5,1)+bytes.fromhex('81010604ff'),('192.168.1.100',52381))

    def test_wire_commands(self):
        self.assertEqual(command(dict(action='move',x=-1,y=-1,speed=3)).hex(), '8101060103030101ff')
        self.assertEqual(command(dict(action='home')).hex(), '81010604ff')
        self.assertEqual(command(dict(action='zoom',direction=1,speed=7)).hex(), '8101040727ff')
        self.assertEqual(command(dict(action='recall',preset=0)).hex(), '8101043f0200ff')
        with self.assertRaises(ValueError): command(dict(action='move',x=8,y=0,speed=3))

    def test_udp_framing_and_stop(self):
        c = Controller()
        c.live = True
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind(('127.0.0.1',0)); receiver.settimeout(1)
            c.config = dict(mode='visca-udp',host='127.0.0.1',port=receiver.getsockname()[1],framing='sony')
            c.send(bytes.fromhex('81010604ff'))
            packet, _ = receiver.recvfrom(1024)
            self.assertEqual(packet, struct.pack('!HHI',0x100,5,1)+bytes.fromhex('81010604ff'))
            c.stop()
            packets = [receiver.recvfrom(1024)[0], receiver.recvfrom(1024)[0]]
            self.assertEqual(packets[0][8:].hex(),'8101060101010303ff')
            self.assertEqual(packets[1][8:].hex(),'8101040700ff')

    def test_config(self):
        self.assertEqual(validate_config({})['mode'],'demo')
        with self.assertRaises(ValueError): validate_config(dict(mode='visca-udp',host='8.8.8.8'))

    def test_http(self):
        c = Controller()
        c.live = True
        server = ThreadingHTTPServer(('127.0.0.1',0),make_handler(c,'test-token'))
        thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        base = 'http://127.0.0.1:%s' % server.server_port
        try:
            with urllib.request.urlopen(base+'/') as response:
                self.assertIn(b'Sony IPELA',response.read())
            req = urllib.request.Request(base+'/api/command',data=b'{"action":"home"}',method='POST')
            with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(req)
            self.assertEqual(error.exception.code,403)
            req.add_header('X-PTZ-Token','test-token')
            with patch.object(c,'send') as send:
                with urllib.request.urlopen(req) as response: self.assertEqual(response.status,200)
                send.assert_called_once_with(bytes.fromhex('81010604ff'))
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__': unittest.main()
