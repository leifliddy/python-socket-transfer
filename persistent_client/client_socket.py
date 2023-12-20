#!/usr/bin/python3

import argparse
import logging
import socket
import sys
import time
from pathlib import Path, PurePath

ip          = '192.168.3.50'
port        = 7000
buffer_size = 1024
tx_dir      = '/tmp/files.tx'


def set_keepalive(sock, after_idle_sec=60, interval_sec=60, max_fails=10):
    """ Set TCP keepalive on an open socket
    It activates after after_idle_sec of idleness,
    then sends a keepalive ping once every interval_sec,
    and closes the connection after max_fails failed ping ()
    """
    logging.debug(f'set_keepalive')
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


def create_socket():
    logging.debug(f'create_socket')
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    client.connect((ip, port))
    return client


def send_files(client):
    logging.debug(f'send_files')
    for file_path in sorted(base_dir.iterdir()):
        if file_path.is_file() and file_path.suffix == '.txt':
            with open(file_path, 'rb') as f:
                logging.info(f'transferring {file_path}')
                while True:
                    bytes_read = f.read(buffer_size)
                    if not bytes_read:
                        break
                    client.sendall(bytes_read)

                file_path.unlink()

            logger.debug('transfer complete')
            time.sleep(0.1)
        else:
            set_keepalive(client)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='display debug messages',
                        default=False)
    parser.add_argument('-q', '--quiet',
                        action='store_true',
                        help='silences all logging output',
                        default=False)
    parser.add_argument('--port',
                        action='store',
                        default=port,
                        help=f'specify the remote port number, default: {port}')
    parser.add_argument('--ip',
                        action='store',
                        default=ip,
                        help=f'specify listening ip address or hostname, default: {ip}')
    parser.add_argument('--txdir',
                        action='store',
                        default=tx_dir,
                        help=f'specify the transmit directory, default: {tx_dir}')

    args = parser.parse_args()
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)-5s]   %(asctime)-17s %(message)s', '%b %d %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.quiet:
        logger.disabled = True
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    base_dir = Path(tx_dir)

    if not base_dir.is_dir():
        logger.info(f'the tx_dir {base_dir} does not exist')
        sys.exit(1)

    client = create_socket()

    while True:
        try:
            send_files(client)
            time.sleep(60)
        except Exception as e:
            logging.error(e)
            logging.debug('sleeping 10 seconds')
            time.sleep(10)
            logging.debug('resuming')
            client.close()
            create_socket()
            pass
