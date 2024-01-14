# plugin based on custom_votes.py by TomTec Solutions.
# govern.py - plugin for non-admin server governance model (vote-based)


# The following cvars are used on this plugin:
#    qlx_disablePlayerRemoval: Prevents non-privileged players from using '/cv kick' or '/cv tempban'. Default: 0
#

#
#    Allowed votes: tempban, spec, do
#

import minqlx
import itertools

class govern(minqlx.Plugin):
    def __init__(self):
        self.add_hook("vote_called", self.handle_vote_called)
        self.add_hook("player_loaded", self.player_loaded)

        self.set_cvar_once("qlx_disablePlayerRemoval", "0")

        self.plugin_version = "1.0"

        # Vote counter. We use this to avoid automatically passing votes we shouldn't.
        self.vote_count = itertools.count()
        self.last_vote = 0

    def player_loaded(self, player):
        if (True):
            pass

    def handle_vote_called(self, caller, vote, args):
        if not (self.get_cvar("g_allowSpecVote", bool)) and caller.team == "spectator":
            if caller.privileges == None:
                caller.tell("You are not allowed to call a vote as spectator.")
                return minqlx.RET_STOP_ALL

        if vote.lower() == "tempban":
            # enables the '/cv tempban <id>' command
            if self.get_cvar("qlx_disablePlayerRemoval", bool):
                # if player removal cvar is set, do not permit '/cv tempban'
                if caller.privileges == None:
                    caller.tell("Voting to tempban is disabled in this server.")
                    caller.tell("^2/cv spec <id>^7 and ^2/cv silence <id>^7 exist as substitutes to kicking.")
                    return minqlx.RET_STOP_ALL
            try:
                player_name = self.player(int(args)).clean_name
                player_id = self.player(int(args)).id
            except:
                caller.tell("^1Invalid ID.^7 Use a client ID from the ^2/players^7 command.")
                return minqlx.RET_STOP_ALL

            if self.player(int(args)).privileges != None:
                caller.tell("The player specified is an admin, a mod or banned, and cannot be tempbanned.")
                return minqlx.RET_STOP_ALL

            self.callvote("tempban {}".format(player_id), "^1ban {} until the map changes^3".format(player_name))
            self.msg("{}^7 called a vote.".format(caller.name))
            return minqlx.RET_STOP_ALL

        if vote.lower() == "spec":
            # enables the '/cv spec <id>' command
            try:
                player_name = self.player(int(args)).clean_name
                player_id = self.player(int(args)).id
            except:
                caller.tell("^1Invalid ID.^7 Use a client ID from the ^2/players^7 command.")
                return minqlx.RET_STOP_ALL

            if self.player(int(args)).team == "spectator":
                caller.tell("That player is already in the spectators.")
                return minqlx.RET_STOP_ALL

            self.callvote("put {} spec".format(player_id), "move {} to the spectators".format(player_name))
            self.msg("{}^7 called a vote.".format(caller.name))
            return minqlx.RET_STOP_ALL

        if vote.lower() == "do":
            if "balance" in self.plugins:
                if self.plugins["balance"].suggested_pair:
                    self.callvote("qlx !do", "force the suggested switch")
                    self.msg("{}^7 called a vote.".format(caller.name))
                else:
                    caller.tell("A switch hasn't been suggested yet by ^4!teams^7, you cannot vote to apply a suggestion that doesn't exist.")
            else:
                caller.tell("The ^4balance^7 system isn't currently loaded. This vote cannot function.")
            return minqlx.RET_STOP_ALL

        # Automatic vote passing.
        if self.get_cvar("qlx_votepass", bool):
            self.last_vote = next(self.vote_count)
            self.force(self.get_cvar("qlx_votepassThreshold", float), self.last_vote)

    @minqlx.delay(29)
    def force(self, require, vote_id):
        if self.last_vote != vote_id:
            # This is not the vote we should be resolving.
            return

        votes = self.current_vote_count()
        if self.is_vote_active() and votes and votes[0] > votes[1]:
            if require:
                teams = self.teams()
                players = teams["red"] + teams["blue"] + teams["free"]
                if sum(votes)/len(players) < require:
                    return
            minqlx.force_vote(True)
