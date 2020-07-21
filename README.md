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
```
{ pkgs, ... }:
let
  botsrc = pkgs.fetchFromGitHub {
    owner = "d6e";
    repo = "discord-talkingstick-bot";
    rev = "9537584d6e9a0fd679716803635b46cb7f98432b";
    sha256 = "1wx8z3fiyz9gfsqs6vsqjmyvlrp5ypbygvc7nzcr6myi1ll5vd55";
  };
  botPath = builtins.toPath "${botsrc}/service.nix";
in {
  imports = [ botPath ];
  services.discordTalkingStickBot.enable = true;
  services.discordTalkingStickBot.secretDiscordToken = "MYSECRET";
}
```
```
nix-instantiate --eval -E '(import <nixpkgs/nixos/lib/eval-config.nix> { modules = [./discordbot.nix]; }).config.systemd.services.discord-talkingstick-bot.description'
```

