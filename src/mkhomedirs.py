
import ldap
import argparse
import getpass
import sys
import os
import os.path
import shutil

VERBOSE = False


def verbose(message):
    global VERBOSE
    if VERBOSE:
        print ':>', message


def mkhomedir(user, uid, gid, homeroot, skel):
    if os.path.isdir(os.path.join(homeroot, user)):
        verbose('Skipping ' + os.path.join(homeroot, user))
        return
    
    verbose("Creating (%s:%s) %s" % (str(uid), str(gid), \
                                     os.path.join(homeroot, user)))
    shutil.copytree(skel, os.path.join(homeroot, user), True)
    for root, dirs, files in os.walk(os.path.join(homeroot, user)):
        os.chown(root, int(uid), int(gid))
        for dir in dirs:
            os.chown(os.path.join(root, dir), int(uid), int(gid))
        for file in files:
            os.chown(os.path.join(root, file), int(uid), int(gid))
    

def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description='Create homedirs via LDAP tree.')
    parser.add_argument('-v', help='Turn on verbosity', action='store_true')
    parser.add_argument('-H', dest='URI', help='LDAP URI', \
                        default='ldap://exmaple.com:389')
    parser.add_argument('-b', dest='BASE', help='LDAP base', \
                        default='ou=users,dc=example,dc=com')
    parser.add_argument('-f', dest='FILTER', help='LDAP filter', \
                        default='(objectClass=posixAccount)')
    parser.add_argument('-D', dest='BINDDN', help='LDAP bind DN', \
                        default='cn=manager')
    parser.add_argument('-w', dest='BINDPASS', help='LDAP bind password', \
                        default='secret')
    parser.add_argument('-W', help='prompt for bind password', action='store_true')
    parser.add_argument('-y', dest='PASSFILE', help='read password from file', \
                        default='')
    parser.add_argument('-a', dest='UNAME', help='username attribute', \
                        default='uid')
    parser.add_argument('-u', dest='UID', help='userid attribute', \
                        default='uidNumber')
    parser.add_argument('-g', dest='GID', help='groupid attribute', \
                        default='gidNumber')
    parser.add_argument('-x', dest='HOMEROOT', help='home dirs root', \
                        default='/home')
    parser.add_argument('-s', dest='SKELETON', help='skeleton dir', \
                        default='/etc/skel')
    args = parser.parse_args()
    
    if args.v:
        VERBOSE = True
        verbose('Enabled verbosity')
    
    if args.W:
        verbose('Reading password from stdin')
        LDAPPASS = getpass.getpass('LDAP bind password: ')
    elif args.PASSFILE != '':
        verbose('Reading password from ' + args.PASSFILE)
        LDAPPASS = open(args.PASSFILE).read().replace('\r', '').replace('\n', '')
    else:
        verbose('Reading password from arguments')
        LDAPPASS = args.BINDPASS
        
    verbose('Connecting to ' + args.URI)
    l = ldap.initialize(args.URI)
    
    verbose('Trying to bind as ' + args.BINDDN)
    if l.simple_bind_s(args.BINDDN, LDAPPASS) is None:
        print "Could not bind"
        sys.exit(1)
    
    verbose('Searching ' + args.FILTER + ' in ' + args.BASE)
    res = l.search_s(args.BASE, ldap.SCOPE_SUBTREE, args.FILTER)
    
    if res is None:
        print "No users found"
        sys.exit(2)
        
    for dn, attrs in res:
        if args.UNAME in attrs and args.UID in attrs and args.GID in attrs:
            mkhomedir(attrs[args.UNAME][0], attrs[args.UID][0], \
                      attrs[args.GID][0], args.HOMEROOT, args.SKELETON)


if __name__ == '__main__':
    main()
