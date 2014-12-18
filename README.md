ftp_rsync_backup
================

This is a little script to perform a rsync backup over a ftp connection. i always searched for a good way to backup my wordpress installations. somehow i never found something i liked to work with. sometimes it placed really large zip files on the server and some of this addons had bugs that they didnt deleted old files so it spaced up the little server and i had to pay some space fee's.

i thought it would be the best way to rsync the folders to my homeserver. i googled around and was dissapointed that rsync doesnt work over ftp by default. so i use some existing components and put it into a script. thanks to fuse, curlftpfs and the almighty rsync.

## Install
1. `git clone https://github.com/xsteadfastx/ftp_rsync_backup.git`
2. `virtualenv venv`
3. `source venv/bin/activate`
4. `cp config.yml.dist config.yml`
