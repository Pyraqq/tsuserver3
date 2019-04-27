import random
import re

from server import logger
from server.exceptions import ClientError, ServerError, ArgumentError

__all__ = [
    'ooc_cmd_roll',
    'ooc_cmd_rollp',
    'ooc_cmd_notecard',
    'ooc_cmd_notecard_clear',
    'ooc_cmd_notecard_reveal',
    'ooc_cmd_rolla_reload',
    'ooc_cmd_rolla_set',
    'ooc_cmd_rolla',
    'ooc_cmd_coinflip'
]


def ooc_cmd_roll(client, arg):
    roll_max = 11037
    if len(arg) != 0:
        try:
            val = list(map(int, arg.split(' ')))
            if not 1 <= val[0] <= roll_max:
                raise ArgumentError(
                    f'Roll value must be between 1 and {roll_max}.')
        except ValueError:
            raise ArgumentError(
                'Wrong argument. Use /roll [<max>] [<num of rolls>]')
    else:
        val = [6]
    if len(val) == 1:
        val.append(1)
    if len(val) > 2:
        raise ArgumentError(
            'Too many arguments. Use /roll [<max>] [<num of rolls>]')
    if val[1] > 20 or val[1] < 1:
        raise ArgumentError('Num of rolls must be between 1 and 20')
    roll = ''
    for i in range(val[1]):
        roll += str(random.randint(1, val[0])) + ', '
    roll = roll[:-2]
    if val[1] > 1:
        roll = '(' + roll + ')'
    client.area.broadcast_ooc('{} rolled {} out of {}.'.format(
        client.char_name, roll, val[0]))
    logger.log_server(
        '[{}][{}]Used /roll and got {} out of {}.'.format(
            client.area.abbreviation, client.char_name, roll, val[0]),
        client)


def ooc_cmd_rollp(client, arg):
    roll_max = 11037
    if len(arg) != 0:
        try:
            val = list(map(int, arg.split(' ')))
            if not 1 <= val[0] <= roll_max:
                raise ArgumentError(
                    f'Roll value must be between 1 and {roll_max}.')
        except ValueError:
            raise ArgumentError(
                'Wrong argument. Use /rollp [<max>] [<num of rolls>]')
    else:
        val = [6]
    if len(val) == 1:
        val.append(1)
    if len(val) > 2:
        raise ArgumentError(
            'Too many arguments. Use /rollp [<max>] [<num of rolls>]')
    if val[1] > 20 or val[1] < 1:
        raise ArgumentError('Num of rolls must be between 1 and 20')
    roll = ''
    for _ in range(val[1]):
        roll += str(random.randint(1, val[0])) + ', '
    roll = roll[:-2]
    if val[1] > 1:
        roll = '(' + roll + ')'
    client.send_ooc('{} rolled {} out of {}.'.format(
        client.char_name, roll, val[0]))

    client.area.broadcast_ooc('{} rolled in secret.'.format(
        client.char_name))
    for c in client.area.owners:
        c.send_ooc('[{}]{} secretly rolled {} out of {}.'.format(
            client.area.abbreviation, client.char_name, roll, val[0]))

    logger.log_server(
        '[{}][{}]Used /rollp and got {} out of {}.'.format(
            client.area.abbreviation, client.char_name, roll, val[0]),
        client)


def ooc_cmd_notecard(client, arg):
    if len(arg) == 0:
        raise ArgumentError('You must specify the contents of the note card.')
    client.area.cards[client.char_name] = arg
    client.area.broadcast_ooc('{} wrote a note card.'.format(
        client.char_name))


def ooc_cmd_notecard_clear(client, arg):
    try:
        del client.area.cards[client.char_name]
        client.area.broadcast_ooc('{} erased their note card.'.format(
            client.char_name))
    except KeyError:
        raise ClientError('You do not have a note card.')


def ooc_cmd_notecard_reveal(client, arg):
    if not client in client.area.owners and not client.is_mod:
        raise ClientError('You must be a CM or moderator to reveal cards.')
    if len(client.area.cards) == 0:
        raise ClientError('There are no cards to reveal in this area.')
    msg = 'Note cards have been revealed.\n'
    for card_owner, card_msg in client.area.cards.items():
        msg += f'{card_owner}: {card_msg}\n'
    client.area.cards.clear()
    client.area.broadcast_ooc(msg)


def ooc_cmd_rolla_reload(client, arg):
    if not client.is_mod:
        raise ClientError(
            'You must be a moderator to load the ability dice configuration.')
    rolla_reload(client.area)
    client.send_ooc('Reloaded ability dice configuration.')


def rolla_reload(area):
    try:
        import yaml
        with open('config/dice.yaml', 'r') as dice:
            area.ability_dice = yaml.load(dice)
    except:
        raise ServerError(
            'There was an error parsing the ability dice configuration. Check your syntax.'
        )


def ooc_cmd_rolla_set(client, arg):
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    available_sets = ', '.join(client.area.ability_dice.keys())
    if len(arg) == 0:
        raise ArgumentError(
            f'You must specify the ability set name.\nAvailable sets: {available_sets}'
        )
    if arg in client.area.ability_dice:
        client.ability_dice_set = arg
        client.send_ooc(f"Set ability set to {arg}.")
    else:
        raise ArgumentError(
            f'Invalid ability set \'{arg}\'.\nAvailable sets: {available_sets}'
        )


def ooc_cmd_rolla(client, arg):
    if not hasattr(client.area, 'ability_dice'):
        rolla_reload(client.area)
    if not hasattr(client, 'ability_dice_set'):
        raise ClientError(
            'You must set your ability set using /rolla_set <name>.')
    ability_dice = client.area.ability_dice[client.ability_dice_set]
    max_roll = ability_dice['max'] if 'max' in ability_dice else 6
    roll = random.randint(1, max_roll)
    ability = ability_dice[roll] if roll in ability_dice else "Nothing happens"
    client.area.broadcast_ooc('{} rolled a {} (out of {}): {}.'.format(
        client.char_name, roll, max_roll, ability))


def ooc_cmd_coinflip(client, arg):
    if len(arg) != 0:
        raise ArgumentError('This command has no arguments.')
    coin = ['heads', 'tails']
    flip = random.choice(coin)
    client.area.broadcast_ooc('{} flipped a coin and got {}.'.format(
        client.char_name, flip))
    logger.log_server(
        '[{}][{}]Used /coinflip and got {}.'.format(client.area.abbreviation,
                                                    client.char_name,
                                                    flip), client)
