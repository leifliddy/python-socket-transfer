#!/usr/bin/python

import argparse
import asyncio
import logging
import pathlib
import socket
import time
from systemd import journal

ip          = socket.gethostbyname(socket.gethostname())
port        = 4455
buffer_size = 1024
rx_dir      = '/home/leif.liddy/Desktop/socket.project/files.rx'


def generate_unique_file_path():
    ms = time.time_ns() // 1_000_000
    file_path = pathlib.PurePath(rx_dir, f'{ms}.txt')
    return file_path


async def service_connection(client):
    loop = asyncio.get_event_loop()
    bytes_read = await loop.sock_recv(client, buffer_size)
    if bytes_read:
        file_path = generate_unique_file_path()
        with open(file_path, 'wb') as f:
            f.write(bytes_read)
            while bytes_read:
                bytes_read = await loop.sock_recv(client, buffer_size)
                f.write(bytes_read)

        logging.info(f'created {file_path}')


async def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen()
    server.setblocking(False)
    loop = asyncio.get_event_loop()

    while True:
        conn, addr = await loop.sock_accept(server)
        logging.debug(f'Accepted connection from {addr}')
        loop.create_task(service_connection(conn))


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
    parser.add_argument('--systemd',
                        action='store_true',
                        help='use the systemd/journald logging mechanism',
                        default=False)
    parser.add_argument('--port',
                        action='store',
                        default=port,
                        help=f'specify port number to listen on, default: {port}')
    parser.add_argument('--ip',
                        action='store',
                        default=ip,
                        help=f'specify listening ip address or hostname, default: {ip}')
    parser.add_argument('--rxdir',
                        action='store',
                        default=rx_dir,
                        help=f'specify the receive directory, default: {rx_dir}')

    args = parser.parse_args()
    logger = logging.getLogger()

    if args.systemd:
        # view logs with:
        # journalctl -b -t py_socket_conn
        logger.addHandler(journal.JournalHandler(SYSLOG_IDENTIFIER='py_socket_conn'))
    else:
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

    while True:
        try:
            asyncio.run(run_server())
        except Exception as e:
            logging.error(e)
            logging.debug('sleeping 10 seconds')
            time.sleep(10)
            logging.debug('resuming')
            pass
