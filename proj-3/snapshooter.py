import os


def create_snap(save_path, timestamp, to_save):
    name = save_path + str(timestamp) + '.snap'
    snap = open(name, 'w')
    for key in to_save.keys():
        if isinstance(to_save[key], type([])):
            snap.write(str(key))
            for val in to_save[key]:
                snap.write('${&*&}$' + str(val))
            snap.write('\n')
        else:
            snap.write(str(key) + '${&*&}$' + str(to_save[key]).replace('\n', '') + '\n')

    snap.write('END_OF_FILE')
    snap.close()


def remove_old_snaps():
    try:
        os.system('rm *.snap')
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
                return result

            line = line.split('${&*&}$')

            if len(line) > 2:
                key = int(line[0])
                values = line[1:]
                result[key] = []

                for value in values:
                    key = int(key)
                    result[key].append(value)
            elif len(line) == 2:
                result[int(line[0])] = line[1]

        snap.close()
        print('Snapshot ' + name + ' was not complete!')
        return {}
    except Exception as ex:
        print(ex)
        exit(0)
