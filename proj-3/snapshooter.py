import ast
import os
import queue
import socket


def create_snap(save_path, timestamp, to_save, ext):
    name = save_path + str(timestamp) + ext
    snap = open(name, 'w')
    for key in to_save.keys():
        snap.write(str(key) + '${&*&}$' + str(to_save[key]) + '\n')

    snap.write('END_OF_FILE')
    remove_old_snaps()
    snap.close()


def move_snaps():
    try:
        if len(os.popen('ls -H *.snap').readlines()) > 0:
            os.system('mv *.snap ./old_rep/')
    except Exception as ex:
        print(ex)


def move_structures():
    try:
        if len(os.popen('ls | grep dir_struct').readlines()) == 0:
            os.system('mkdir dir_struct')

        os.system('mv *.struct dir_struct')
    except Exception as ex:
        print(ex)


def remove_old_snaps():
    try:
        if len(os.popen('ls ./old_rep/').readlines()) > 0:
            os.system('rm ./old_rep/*')
        if len(os.popen('ls | grep .log').readlines()) > 0:
            os.system('rm *.log')
        # os.system('rm $(ls -I ' + name + ' | grep .snap)')
    except Exception as ex:
        print(ex)


def reload_snap(name):
    try:
        snap = open(name, 'r')
        result = {}
        for line in snap:
            if 'END_OF_FILE' in line:
                snap.close()
                return result

            line = line.split('${&*&}$')

            if len(line) == 2:
                try:
                    result[int(line[0])] = ast.literal_eval(line[1])
                except Exception:
                    result[int(line[0])] = line[1].replace('\n', '')

        snap.close()
        print('Snapshot ' + name + ' was not complete!')
        return None
    except Exception as ex:
        print(ex)
        exit(0)


def save_structs(save_path, timestamp, to_save, ext):
    name = save_path + str(timestamp) + ext
    snap = open(name, 'w')

    for key in to_save.keys():
        snap.write(str(key) + '\n')

    snap.write('END_OF_FILE')
    snap.close()


def remove_old_structs():
    try:
        if len(os.popen('ls | grep dir_struct').readlines()) > 0:
            if len(os.popen('ls ./dir_struct/').readlines()) > 0:
                os.system('rm ./dir_struct/*')
    except Exception as ex:
        print(ex)


def retrieve_structs(name):
    try:
        snap = open(name, 'r')
        result = {}
        pid_list = []
        for line in snap:
            if 'END_OF_FILE' in line:
                snap.close()
                return result, pid_list

            pid_list.append(int(line))
            result[int(line)] = {
                'commands': queue.Queue(),
                'sock': socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                'response': queue.Queue()
            }

        snap.close()
        print('Snapshot ' + name + ' was not complete!')
        return None
    except Exception as ex:
        print(ex)
        exit(0)
