import binascii
import re

from Crypto.Cipher import AES


def webvpn(url):

    encryStr = b'wrdvpnisthebest!'

    def encrypt(url):
        url = str.encode(url)
        cryptor = AES.new(encryStr, AES.MODE_CFB, encryStr, segment_size=16*8)

        return bytes.decode(binascii.b2a_hex(encryStr)) + \
            bytes.decode(binascii.b2a_hex(cryptor.encrypt(url)))

    if url[0:7] == 'http://':
        url = url[7:]
        protocol = 'http'
    elif url[0:8] == 'https://':
        url = url[8:]
        protocol = 'https'

    v6 = re.match('[0-9a-fA-F:]+', url)
    if v6 != None:
        v6 = v6.group(0)
        url = url[len(v6):]

    segments = url.split('?')[0].split(':')
    port = None
    if len(segments) > 1:
        port = segments[1].split('/')[0]
        url = url[0: len(segments[0])] + url[len(segments[0]) + len(port) + 1:]

    try:
        idx = url.index('/')
        host = url[0: idx]
        path = url[idx:]
        if v6 != None:
            host = v6
        url = encrypt(host) + path
    except:
        if v6 != None:
            url = v6
        url = encrypt(url)

    if port != None:
        url = 'https://webvpn.tsinghua.edu.cn/' + protocol + '-' + port + '/' + url
    else:
        url = 'https://webvpn.tsinghua.edu.cn/' + protocol + '/' + url

    return url
