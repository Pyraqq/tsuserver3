from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, ArgumentError, AreaError

__all__ = [
    'ooc_cmd_a',
    'ooc_cmd_s',
    'ooc_cmd_g',
    'ooc_cmd_gm',
    'ooc_cmd_m',
    'ooc_cmd_lm',
    'ooc_cmd_announce',
    'ooc_cmd_toggleglobal',
    'ooc_cmd_need',
    'ooc_cmd_toggleadverts',
    'ooc_cmd_pm',
    'ooc_cmd_mutepm'
]


def ooc_cmd_a(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify an area.')
    arg = arg.split(' ')

    try:
        area = client.server.area_manager.get_area_by_id(int(arg[0]))
    except AreaError:
        raise

    message_areas_cm(client, [area], ' '.join(arg[1:]))


def ooc_cmd_s(client, arg):
    areas = []
    for a in client.server.area_manager.areas:
        if client in a.owners:
            areas.append(a)
    if not areas:
        client.send_ooc('You aren\'t a CM in any area!')
        return
    message_areas_cm(client, areas, arg)


def message_areas_cm(client, areas, message):
    for a in areas:
        if not client in a.owners:
            client.send_ooc(f'You are not a CM in {a.name}!')
            return
        a.send_command('CT', client.name, message)
        a.send_owner_command('CT', client.name, message)


def ooc_cmd_g(client, arg):
    if client.muted_global:
        raise ClientError('Global chat toggled off.')
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.broadcast_global(client, arg)
    logger.log_server(
        '[{}][{}][GLOBAL]{}.'.format(client.area.abbreviation,
                                     client.char_name, arg), client)


def ooc_cmd_gm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if client.muted_global:
        raise ClientError('You have the global chat muted.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.broadcast_global(client, arg, True)
    logger.log_server(
        '[{}][{}][GLOBAL-MOD]{}.'.format(client.area.abbreviation,
                                         client.char_name, arg), client)
    logger.log_mod(
        '[{}][{}][GLOBAL-MOD]{}.'.format(client.area.abbreviation,
                                         client.char_name, arg), client)


def ooc_cmd_m(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("You can't send an empty message.")
    client.server.send_modchat(client, arg)
    logger.log_server(
        '[{}][{}][MODCHAT]{}.'.format(client.area.abbreviation,
                                      client.char_name, arg), client)
    logger.log_mod(
        '[{}][{}][MODCHAT]{}.'.format(client.area.abbreviation,
                                      client.char_name, arg), client)


def ooc_cmd_lm(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.area.send_command(
        'CT', '{}[MOD][{}]'.format(client.server.config['hostname'],
                                   client.char_name), arg)
    logger.log_server(
        '[{}][{}][LOCAL-MOD]{}.'.format(client.area.abbreviation,
                                        client.char_name, arg), client)
    logger.log_mod(
        '[{}][{}][LOCAL-MOD]{}.'.format(client.area.abbreviation,
                                        client.char_name, arg), client)


def ooc_cmd_announce(client, arg):
    if not client.is_mod:
        raise ClientError('You must be authorized to do that.')
    if len(arg) == 0:
        raise ArgumentError("Can't send an empty message.")
    client.server.send_all_cmd_pred(
        'CT', '{}'.format(client.server.config['hostname']),
        f'=== Announcement ===\r\n{arg}\r\n==================', '1')
    logger.log_server(
        '[{}][{}][ANNOUNCEMENT]{}.'.format(client.area.abbreviation,
                                           client.char_name, arg),
        client)
    logger.log_mod(
        '[{}][{}][ANNOUNCEMENT]{}.'.format(client.area.abbreviation,
                                           client.char_name, arg),
        client)


def ooc_cmd_toggleglobal(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_global = not client.muted_global
    glob_stat = 'on'
    if client.muted_global:
        glob_stat = 'off'
    client.send_ooc(f'Global chat turned {glob_stat}.')


def ooc_cmd_need(client, arg):
    if client.muted_adverts:
        raise ClientError('You have advertisements muted.')
    if len(arg) == 0:
        raise ArgumentError("You must specify what you need.")
    client.server.broadcast_need(client, arg)
    logger.log_server(
        '[{}][{}][NEED]{}.'.format(client.area.abbreviation,
                                   client.char_name, arg), client)


def ooc_cmd_toggleadverts(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.muted_adverts = not client.muted_adverts
    adv_stat = 'on'
    if client.muted_adverts:
        adv_stat = 'off'
    client.send_ooc(f'Advertisements turned {adv_stat}.')


def ooc_cmd_pm(client, arg):
    args = arg.split()
    key = ''
    msg = None
    if len(args) < 2:
        raise ArgumentError(
            'Not enough arguments. use /pm <target> <message>. Target should be ID, OOC-name or char-name. Use /getarea for getting info like "[ID] char-name".'
        )
    targets = client.server.client_manager.get_targets(client,
                                                       TargetType.CHAR_NAME,
                                                       arg, True)
    key = TargetType.CHAR_NAME
    if len(targets) == 0 and args[0].isdigit():
        targets = client.server.client_manager.get_targets(
            client, TargetType.ID, int(args[0]), False)
        key = TargetType.ID
    if len(targets) == 0:
        targets = client.server.client_manager.get_targets(
            client, TargetType.OOC_NAME, arg, True)
        key = TargetType.OOC_NAME
    if len(targets) == 0:
        raise ArgumentError('No targets found.')
    try:
        if key == TargetType.ID:
            msg = ' '.join(args[1:])
        else:
            if key == TargetType.CHAR_NAME:
                msg = arg[len(targets[0].char_name) + 1:]
            if key == TargetType.OOC_NAME:
                msg = arg[len(targets[0].name) + 1:]
    except:
        raise ArgumentError(
            'Not enough arguments. Use /pm <target> <message>.')
    c = targets[0]
    if c.pm_mute:
        raise ClientError('This user muted all pm conversation')
    else:
        if c.is_mod:
            c.send_ooc(
                'PM from {} (ID: {}, IPID: {}) in {} ({}): {}'.format(
                    client.name, client.id, client.ipid, client.area.name,
                    client.char_name, msg))
        else:
            c.send_ooc('PM from {} (ID: {}) in {} ({}): {}'.format(
                client.name, client.id, client.area.name,
                client.char_name, msg))
        client.send_ooc('PM sent to {}. Message: {}'.format(
            args[0], msg))


def ooc_cmd_mutepm(client, arg):
    if len(arg) != 0:
        raise ArgumentError("This command doesn't take any arguments")
    client.pm_mute = not client.pm_mute
    client.send_ooc('You stopped receiving PMs' if client.
                             pm_mute else 'You are now receiving PMs')
