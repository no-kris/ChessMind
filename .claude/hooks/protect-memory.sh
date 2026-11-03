#!/usr/bin/env bash
# PreToolUse hook (Bash): keep .memory/knowledge and .memory/reference read-only.
# A command that touches either folder is allowed only if every segment is a
# known read-only command; anything else (redirects, rm, mv, sed -i, ...) is denied.

input=$(cat)
cmd=$(jq -r '.tool_input.command // ""' <<<"$input")
cwd=$(jq -r '.cwd // ""' <<<"$input")

protected='\.memory/(knowledge|reference)'
touches=0
if grep -Eq "$protected" <<<"$cmd"; then touches=1; fi
if grep -Eq "$protected(/|$)" <<<"$cwd"; then touches=1; fi
if grep -Eq '/\.memory/?$' <<<"$cwd" && grep -Eq '(^|[^A-Za-z0-9_])(knowledge|reference)([^A-Za-z0-9_]|$)' <<<"$cmd"; then touches=1; fi
[ "$touches" -eq 0 ] && exit 0

deny() {
  jq -n --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: (".memory/knowledge and .memory/reference are read-only: " + $r)}}'
  exit 0
}

# Command substitution can hide arbitrary commands.
if grep -Eq '\$\(|`' <<<"$cmd"; then deny "command substitution is not allowed here"; fi

# Any output redirect other than to /dev/null or fd duplication.
stripped=$(sed -E 's/[0-9]*>&[0-9-]+//g; s/&?[0-9]*>>?[[:space:]]*\/dev\/null//g' <<<"$cmd")
if grep -q '>' <<<"$stripped"; then deny "output redirection is not allowed"; fi

readonly_cmds=' cat head tail less more grep egrep fgrep rg ls stat file wc find tree du diff cmp jq sort uniq cut tr echo printf realpath readlink basename dirname test [ true md5sum sha256sum sed git cd pwd '

while IFS= read -r seg; do
  seg=$(sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' <<<"$seg")
  [ -z "$seg" ] && continue
  read -r first second _ <<<"$seg"
  case "$readonly_cmds" in *" $first "*) ;; *) deny "'$first' is not a read-only command" ;; esac
  case "$first" in
    find) grep -Eq -- '-(delete|exec|execdir|ok|okdir|fprint|fprintf|fls)' <<<"$seg" && deny "find with -delete/-exec is not allowed" ;;
    sed)  grep -Eq -- '(^|[[:space:]])-[a-zA-Z]*i|--in-place' <<<"$seg" && deny "sed -i is not allowed" ;;
    git)  case "$second" in log|diff|show|status|ls-files|blame|grep) ;; *) deny "'git $second' is not read-only" ;; esac ;;
  esac
done < <(sed -E 's/(&&|\|\||;|\||&)/\n/g' <<<"$cmd")

exit 0
