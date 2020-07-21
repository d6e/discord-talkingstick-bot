{ config, lib, pkgs, ... }:
let
  discordTalkingStickBot = pkgs.callPackage ./default.nix {};

  cfg = config.services.discordTalkingStickBot;
in {
    options.services.discordTalkingStickBot.enable = lib.mkEnableOption "Discord TalkingStick Bot";
    options.services.discordTalkingStickBot.secretDiscordToken = lib.mkOption {
        type = lib.types.str;
        default = "";
    };
    options.services.discordTalkingStickBot.extraArgs = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [""];
        example = ["--debug"];
    };

    config = lib.mkIf cfg.enable {
        # networking.firewall.allowedTCPPorts = [ cfg.port ];

        systemd.services.discord-talkingstick-bot = {
            description = "A discord bot for one-person-at-a-time communication in discord voice chats.";
            environment = {
                PYTHONUNBUFFERED = "1";
                DISCORD_BOT_SECRET = cfg.secretDiscordToken;
            };
            after = [ "network-online.target" ];
            wantedBy = [ "multi-user.target" ];
            serviceConfig = {
                Type = "simple";
                DynamicUser = "true";
                ExecStart = "${discordTalkingStickBot}/bin/bot.py ${lib.concatStringsSep " " cfg.extraArgs}";
                #ExecStop = "${pkgs.procps}/bin/pkill --signal SIGINT bot.py";
                #TimeoutStopSec = 30;
                KillSignal = "SIGINT";
                KillMode = "process";
                Restart = "on-abnormal";
                RestartSec = "60";
            };
        };
    };
}
