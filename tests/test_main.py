import yaml
import tempfile
import os
import pytest
import shutil
import mock

from ftp_rsync_backup import (
    build_command_list,
    run_backup,
    from_file,
    main)


@pytest.fixture
def config_file(request):
    """Create test config file and removes it afterwards.
    """
    config = {
        'test_backup': {
            'server': 'testserver',
            'user': 'testuser',
            'password': 'testpassword',
            'destination': 'testdir'}}

    temp_dir = tempfile.mkdtemp()
    configfile = os.path.join(temp_dir, 'config.yml')

    with open(configfile, 'w') as open_configfile:
        open_configfile.write(yaml.dump(config))

    def fin():
        """Delete tempdir after fixture is not needed anymore.
        """
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass

    request.addfinalizer(fin)
    return configfile


@pytest.fixture
def mountpoint(request):
    """Creates temp mountpoint.
    """
    directory = tempfile.mkdtemp()

    def fin():
        """Delete tempdirl after fixture is not needed anymore.
        """
        try:
            shutil.rmtree(directory)
        except OSError:
            pass

    request.addfinalizer(fin)
    return directory


def test_build_command_list(config_file):
    """Function build_command_list builds expected commands.
    """
    temp_mountpoint = '/tmp/mountpoint'

    with open(config_file, 'r') as open_configfile:
        config = yaml.load(open_configfile)

    expected_cmds = [
        'curlftpfs ftp://{}:{}@{} {}'.format('testuser',
                                             'testpassword',
                                             'testserver',
                                             temp_mountpoint),
        'rsync -uvrz --delete {}/ {}'.format(temp_mountpoint, 'testdir'),
        'fusermount -u {}'.format(temp_mountpoint)]

    commands = build_command_list(config['test_backup']['server'],
                                  config['test_backup']['user'],
                                  config['test_backup']['password'],
                                  temp_mountpoint,
                                  config['test_backup']['destination'])

    assert commands == expected_cmds


@mock.patch('ftp_rsync_backup.subprocess')
def test_run_backup(subprocess, config_file):
    """Function run_backup works as expected.
    """
    # mock stuff
    subprocess.Popen.return_value.returncode = 0

    # bogus mountpoint
    temp_mountpoint = '/tmp/mountpoint'

    # load test config
    with open(config_file, 'r') as open_configfile:
        config = yaml.load(open_configfile)

    # command list
    commands = build_command_list(config['test_backup']['server'],
                                  config['test_backup']['user'],
                                  config['test_backup']['password'],
                                  temp_mountpoint,
                                  config['test_backup']['destination'])

    # run it
    logfile = '/tmp/logfile'
    run_backup(commands, logfile)

    # testing if subprocess got called 3 times
    assert subprocess.Popen.call_count == 3

    # getting subprocess calls
    calls = subprocess.Popen.call_args_list

    # list of expected commands
    expected_cmds = [
        'curlftpfs ftp://{}:{}@{} {}'.format('testuser',
                                             'testpassword',
                                             'testserver',
                                             temp_mountpoint),
        'rsync -uvrz --delete {}/ {}'.format(temp_mountpoint, 'testdir'),
        'fusermount -u {}'.format(temp_mountpoint)]

    # check if call and response are the same
    for call, response in zip(calls, expected_cmds):
        call_args, call_kwargs = call

        assert call_args[0] == response


@mock.patch('ftp_rsync_backup.subprocess')
def test_from_file(subprocess, config_file, mountpoint):
    """Function from_file works as expected.
    """
    # set arguments
    arguments = {}
    arguments['<config>'] = config_file

    # mock stuff
    subprocess.Popen.return_value.returncode = 0

    # bogus mountpoint

    # run it
    from_file(arguments, mountpoint=mountpoint)

    # testing if subprocess got called 3 times
    assert subprocess.Popen.call_count == 3

    # getting subprocess calls
    calls = subprocess.Popen.call_args_list

    # list of expected commands
    expected_cmds = [
        'curlftpfs ftp://{}:{}@{} {}'.format('testuser',
                                             'testpassword',
                                             'testserver',
                                             mountpoint),
        'rsync -uvrz --delete {}/ {}'.format(mountpoint, 'testdir'),
        'fusermount -u {}'.format(mountpoint)]

    # check if call and response are the same
    for call, response in zip(calls, expected_cmds):
        call_args, call_kwargs = call

        assert call_args[0] == response

    # test return code in logfile
    logfile = 'test_backup.log'

    with open(logfile) as open_logfile:
        assert open_logfile.readlines()[0] == 'Exit Code: 0'

    subprocess.Popen.return_value.returncode = 1

    from_file(arguments, mountpoint)

    with open(logfile) as open_logfile:
        assert open_logfile.readlines()[0] == 'Exit Code: 1'


@mock.patch('ftp_rsync_backup.find_executable')
@mock.patch('ftp_rsync_backup.subprocess')
def test_main_function(subprocess, find_executable, config_file, capsys):
    """main function works as expected.
    """
    # set arguments
    arguments = {
        '--file': True,
        '--help': False,
        '-f': False,
        '-h': False,
        '<config>': '{}'.format(config_file)}

    # mocking
    find_executable.return_value = None
    subprocess.Popen.return_value.returncode = 0

    # run main
    main(arguments)

    # read stdout and stderr
    out, err = capsys.readouterr()

    assert out == 'Please install rsync and curlftpfs\n'

    # mock again
    find_executable.return_value = '/usr/bin/rsync'

    # run main
    main(arguments)

    # testing if subprocess got called 3 times
    assert subprocess.Popen.call_count == 3
