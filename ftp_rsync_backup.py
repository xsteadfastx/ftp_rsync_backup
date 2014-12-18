"""
Usage:
    ftp_rsync_backup.py -f <config> | --file <config>
    ftp_rsync_backup.py -h | --help
"""
import subprocess
import tempfile
import yaml
import shutil
from distutils.spawn import find_executable
from docopt import docopt


def build_command_list(server, user, password, mountpoint, backupdir):
    """Function to build a list of all commands to run the backup.
    """
    commands = []

    commands.append(
        'curlftpfs ftp://{}:{}@{} {}'.format(user,
                                             password,
                                             server,
                                             mountpoint))

    commands.append(
        'rsync -uvrz --delete {}/ {}'.format(mountpoint, backupdir))

    commands.append('fusermount -u {}'.format(mountpoint))

    return commands


def run_backup(commands, logfile):
    """Takes the a list of commands and runs them one after another.
    """
    first_cmd = True
    return_codes = []

    for cmd in commands:
        if first_cmd:
            open_mode = 'w'
            first_cmd = False
        else:
            open_mode = 'a'

        # run process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True)

        # write logfile
        with open(logfile, open_mode) as open_logfile:
            for line in proc.stdout:
                open_logfile.write(line.decode('utf-8'))
            proc.wait()

        # store return code
        return_codes.append(proc.returncode)

    # write exit code
    code = 0
    for return_code in return_codes:
        if return_code != 0:
            code = 1

    # write exitcode to log
    with open(logfile, 'a') as open_logfile:
        open_logfile.write('Exit Code: {}'.format(code))


def from_file(arguments, mountpoint=tempfile.mkdtemp()):
    """Reading config from file and running backup.
    """
    # reading yaml file
    with open(arguments['<config>'], 'r') as open_configfile:
        config = yaml.load(open_configfile)

    # work through config file
    for scalar, sequence in config.items():
        # some variables
        logfile = '{}.log'.format(scalar)

        # command list
        commands = build_command_list(
            sequence['server'],
            sequence['user'],
            sequence['password'],
            mountpoint,
            sequence['destination'])

        # run backup
        run_backup(commands, logfile)

        # remove mountpoint
        try:
            shutil.rmtree(mountpoint)
        except OSError:
            pass


if __name__ == '__main__':
    if find_executable('curlftpfs') and find_executable('rsync'):
        ARGUMENTS = docopt(__doc__)
        if ARGUMENTS['--file'] or ARGUMENTS['-f']:
            from_file(ARGUMENTS)
    else:
        print('Please install rsync and curlftpfs')
