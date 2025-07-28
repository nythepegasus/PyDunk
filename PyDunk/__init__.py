
from . import auth, utils, xcode

import json
from uuid import uuid4 as u4
import questionary
import click
from pprint import pp as _pp
import shutil

def pp(obj, width: int = 0, *args, **kwargs):
    width = shutil.get_terminal_size((120, 80)).columns if width == 0 else width
    _pp(obj, *args, **kwargs, width=width)

from .utils.anisette import Anisette, AniV3Sync, to_dict, from_dict, from_file, to_file
from .auth import GSUserAuth, GSAuthSync
from .xcode.session import XcodeAPI

from anisettev3 import MAIN_ANI

def read_config(path: str):
    with open(path, "r") as f:
        d = json.load(f)
        return d["email"], d["password"], from_dict(d["anisette"])

@click.group()
def cli():
    pass

@cli.group(name="xcode")
@click.option('--config', '-c', type=click.Path())
@click.option('--anisette', '-a', type=click.Path())
@click.option('--email', '-e', type=str)
@click.option('--password', '-p', type=str)
@click.pass_context
def xcode_cli(ctx, config, anisette, email, password):
    ctx.ensure_object(dict)
    try:
        if config is not None:
            email, password, ani = read_config(config)
        else:
            anisette = questionary.path("Which anisette config should be used?").skip_if(anisette is not None, anisette).ask()
            try:
                ani = from_file(anisette)
            except FileNotFoundError:
                ani = AniV3Sync(MAIN_ANI)
                to_file(anisette, ani)
            email = questionary.text("Email: ").skip_if(email is not None, email).ask()
            password = questionary.password("Password: ").skip_if(password is not None, password).ask()
        if any(d == None for d in [ani, email, password]): return
        ctx.obj['x'] = XcodeAPI.from_gsauth(GSAuthSync(GSUserAuth(email, password, Anisette(ani.url, ani))), verify=False) # type: ignore
    except FileNotFoundError:
        anisette = questionary.path("Which anisette config should be used?").skip_if(anisette is not None, anisette).ask()
        try:
            ani = from_file(anisette)
        except FileNotFoundError:
            ani = AniV3Sync(MAIN_ANI)
            to_file(anisette, ani)
        email = questionary.text("Email: ").skip_if(email is not None, email).ask()
        password = questionary.password("Password: ").skip_if(password is not None, password).ask()
        if any(d == None for d in [ani, email, password]): return
        ctx.obj['x'] = XcodeAPI.from_gsauth(GSAuthSync(GSUserAuth(email, password, Anisette(ani.url, ani))), verify=False) # type: ignore
        with open(config, "w") as f:
            json.dump({
                "email": email,
                "password": password,
                "anisette": to_dict(ani)
            }, f, indent=2)
        

@xcode_cli.command()
@click.option('--output', '-o', type=click.Path())
@click.option('--redact', '-r', type=bool, default=True)
@click.pass_context
def debug(ctx, output: str | None, redact: bool):
    x: XcodeAPI = ctx.obj['x']
    debug_out = {'teams': {}}
    for t in x.teams:
        tid = t.team_id
        debug_out['teams'][tid] = {k: v for k, v in t.__dict__.items() if k != '_x'} | {'appids': {}, 'devices': {}, 'profiles': {}}
        if redact:
            team = debug_out['teams'].pop(tid)
            tid = str(u4())
            team["current_member"] = {"roles": team["current_member"]["roles"]}
            team['team_id'] = tid
            team['name'] = str(u4())
            for i, _ in enumerate(team['memberships']):
                membership = team['memberships'].pop(i)
                membership['membershipId'] = str(u4())
                team['memberships'].insert(i, membership)
            debug_out['teams'][tid] = team

        if t.app_ids:
            for a in t.app_ids:
                debug_out['teams'][tid]['appids'][a.app_id] = {k: v for k, v in a.__dict__.items() if k != '_x'}
                if redact:
                    app_id = debug_out['teams'][tid]['appids'].pop(a.app_id)
                    app_id['app_id'] = str(u4())
                    app_id['prefix'] = tid
                    app_id['name'] = str(u4())
                    app_id['identifier'] = str(u4())
                    debug_out['teams'][tid]['appids'][app_id['app_id']] = app_id

        if t.devices:
            for d in t.devices:
                debug_out['teams'][tid]['devices'][d.device_id] = {k: v for k, v in d.__dict__.items() if k != '_x'}
                if redact:
                    device = debug_out['teams'][tid]['devices'].pop(d.device_id)
                    device['device_id'] = str(u4())
                    device['name'] = str(u4())
                    device['device_number'] = str(u4())
                    device['model'] = str(u4())
                    debug_out['teams'][tid]['devices'][device['device_id']] = device

        if t.profiles:
            for p in t.profiles['data']:
                debug_out['teams'][tid]['profiles'][p['id']] = p
                if redact:
                    profile = debug_out['teams'][tid]['profiles'].pop(p['id'])
                    profile['id'] = str(u4())
                    profile['attributes']['name'] = str(u4())
                    profile.pop('links')
                    profile.pop('relationships')
                    profile['attributes'].pop('profileContent')
                    debug_out['teams'][tid]['profiles'][profile['id']] = profile

        if t.capabilities: debug_out['teams'][tid]['capabilities'] = t.capabilities
    if output is None: return click.echo(json.dumps(debug_out, indent=2, default=str))
    with open(output, "w") as f: json.dump(debug_out, f, indent=2, default=str)

@xcode_cli.command()
@click.pass_context
def login(ctx):
    pp("Logging in")
    pp(ctx.obj['x'].account)

@xcode_cli.group(invoke_without_command=True)
@click.pass_context
def teams(ctx):
    x = ctx.obj['x']
    if ctx.invoked_subcommand is None:
        pp(x.teams)

@teams.command(name="list")
@click.pass_context
def list_teams(ctx):
    x = ctx.obj['x']
    pp(x.teams)

@xcode_cli.group(invoke_without_command=True)
@click.pass_context
def devices(ctx):
    x = ctx.obj['x']
    if ctx.invoked_subcommand is None:
        pp(x.teams[0].devices)

@devices.command(name="list")
@click.pass_context
def list_devices(ctx):
    x = ctx.obj['x']
    pp(x.teams[0].devices)

@devices.command(name="add")
@click.argument("name")
@click.argument("udid")
@click.pass_context
def add_device(_, name, udid):
    click.echo(f"TODO\nAdding device {name!r} with {udid!r}!")

@xcode_cli.group(invoke_without_command=True)
@click.pass_context
def appids(ctx):
    x = ctx.obj['x']
    if ctx.invoked_subcommand is None:
        pp(x.teams[0].app_ids)

@appids.command(name="list")
@click.pass_context
def list_appids(ctx):
    x = ctx.obj['x']
    pp(x.teams[0].app_ids)

@xcode_cli.group(invoke_without_command=True)
@click.pass_context
def appgroups(ctx):
    x = ctx.obj['x']
    if ctx.invoked_subcommand is None:
        pp(x.teams[0].qh_app_groups)

@appgroups.command(name="list")
@click.pass_context
def list_appgroups(ctx):
    x = ctx.obj['x']
    pp(x.teams[0].qh_app_groups)

cli(obj={})
