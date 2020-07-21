## Setup
1. Create a new app at https://discord.com/developers then create a bot and set the environment variable `DISCORD_BOT_SECRET` to the bot's secret token.
2. Create a role with permissions on the server for any permissions the bot requests.
3. `https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions=4202496`

## TODO
- [ ] timed talking stick
  * with 30 sec warning
  * command line timer parameter
- [ ] next member command

# Nixos Install
I named the following `discordbot.nix` and imported it into to my configuration.nix.
```
{ pkgs, ... }:
let
  # This has to be the local path to the git repo since you can't fetch during evaluation.
  # I may be doing this all wrong, I'm still learning nixos.
  botsrc = "/home/d6e/src/gitlab.com/d6e/discord-talkingstick-bot";
  botPath = builtins.toPath "${botsrc}/service.nix";
in {
  imports = [ botPath ];
  services.discordTalkingStickBot.enable = true;
  services.discordTalkingStickBot.secretDiscordToken = "MYSECRET";
}
```

You can test that it evaluates with this:
```
nix-instantiate --eval -E '(import <nixpkgs/nixos/lib/eval-config.nix> { modules = [./discordbot.nix]; }).config.systemd.services.discord-talkingstick-bot.description'
```
