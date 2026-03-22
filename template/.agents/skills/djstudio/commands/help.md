Print user documentation for a djstudio subcommand.

Parse `$ARGUMENTS` as: `[command_name]`

If no `command_name` is given:
1. Print the full subcommand table (same output as `/djstudio` with no arguments).
2. Stop — do not execute any other instructions.

Otherwise:
1. Read `.claude/commands/djstudio/<command_name>.md`.
   If the file does not exist, say:
   > Unknown subcommand: `<command_name>`. Run `/djstudio help` for a list of subcommands.
   Then stop.
2. Find the `## Help` section in that file.
3. Print its contents verbatim to the user.
4. Stop — do not execute any other instructions in the file.

---

## Help

**djstudio help [<command>]**

Prints documentation for a djstudio subcommand.

With no argument, lists all available subcommands. With a command name, prints that
command's usage, arguments, and examples.

Examples:
  /djstudio help
  /djstudio help create-cron
  /djstudio help create-model
