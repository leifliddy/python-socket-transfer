#!/usr/bin/python

import argparse
import logging
import socket
import time
import sys
from pathlib import Path, PurePath
 
 
ip          = socket.gethostbyname(socket.gethostname())
port        = 4455
buffer_size = 1024
tx_dir      = '/home/leif.liddy/Desktop/socket.project/files.tx'


if __name__ == "__main__":

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
                        help=f'specify port number to listen on, default: {port}')
    parser.add_argument('--ip',
                        action='store',
                        default=ip,
                        help=f'specify listening ip address or hostname, default: {ip}')
    parser.add_argument('--txdir',
                        action='store',
                        default=tx_dir,
                        help=f'specify the receive directory, default: {tx_dir}')

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
        
    for file_path in sorted(base_dir.iterdir()):
        if file_path.is_file() and file_path.suffix == '.txt':
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((ip, port))
                with open(file_path, 'rb') as f:
                    logging.info(f'transferring {file_path}')
                    while True:
                        bytes_read = f.read(buffer_size)
                        if not bytes_read:
                            break
                        client.sendall(bytes_read)
             time.sleep(0.1)
             logging.debug(f'removing {file_path}')                    
             file_path.unlink()
