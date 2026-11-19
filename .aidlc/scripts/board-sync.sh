#!/usr/bin/env bash
# Board sync (v2, AI-DLC kit: adds Release column and phase:6-release): keeps issue labels in step with the Project board.
#
# People move cards between Status columns. This script notices the move,
# sets the labels that match the column (the labels AGENTS.md reads),
# assigns the phase owner and posts the phase's exit checklist.
# It never moves a card.
#
# v2: it remembers the last column it announced on each issue (a hidden
# marker in its own comment). It posts the checklist only when the card is in
# a new column. If the labels drift while the card stays put (a person or an
# AI session changed a label, or GitHub returned stale data), it puts the
# labels back without posting anything.
#
# Assignees: when a card reaches a column that has an owner, that owner
# becomes the assignee and the previous phase owner is removed. Other
# assignees (people who aren't phase owners) are left alone. Ready and Done
# have no owner, so assignees don't change there.
#
# Options (environment):
#   DRY_RUN=1          log the gh calls it would make instead of making them
#   BOARD_JSON=<file>  read a captured board.json instead of querying GitHub
set -euo pipefail

if [ -z "${BOARD_JSON:-}" ]; then : "${ORG:?}" "${PROJECT_NUMBER:?}"; fi
: "${GITHUB_REPOSITORY:?}"
MINUTES="${MINUTES:-0}"
INTERVAL="${INTERVAL:-20}"
DRY_RUN="${DRY_RUN:-0}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
# Comments read per issue to find the last marker (GitHub's page maximum).
COMMENT_WINDOW=100

# Issues announced or repaired during this run (demo mode makes several
# passes; the board can still show old labels a few seconds after an edit).
declare -A announced_now=()
declare -A repaired_now=()
# Unknown columns already reported during this run.
declare -A unknown_seen=()
# Issues whose update failed during this run.
failures=0

# Scratch files live in a private temp folder, never in the checkout.
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

log() { echo "$*"; echo "- $*" >> "$SUMMARY"; }

# A failed update skips that issue only; the next run retries it.
fail_issue() {
  echo "::error::#$1: $2. Skipped this issue; the next run retries it."
  echo "- **#$1: $2.** Skipped; the next run retries it." >> "$SUMMARY"
  failures=$((failures + 1))
}

# A failed assignee change doesn't stop the labels or the comment.
warn_issue() {
  echo "::error::#$1: $2. Labels and the comment were still updated."
  echo "- **#$1: $2.** Labels and the comment were still updated." >> "$SUMMARY"
  failures=$((failures + 1))
}

# GitHub usernames compare without case and without a leading "@".
login() { sed 's/^@//' <<<"$1" | tr '[:upper:]' '[:lower:]'; }

# Every phase owner from the OWNER_* repo variables, one per line.
phase_owners() {
  for o in "${OWNER_PRODUCT:-}" "${OWNER_DESIGN:-}" "${OWNER_TECH:-}" "${OWNER_ENG:-}" "${OWNER_RELEASE:-}"; do
    [ -n "$o" ] && login "$o"
  done | sort -u
}

# Every write to GitHub goes through here.
write_gh() {
  if [ "$DRY_RUN" = 1 ]; then
    echo "DRY RUN: gh $*"
    if [ "$1 $2" = "issue comment" ]; then sed -n '1,2s/^/    | /p' "$WORK/comment.md"; fi
    return 0
  fi
  gh "$@" < /dev/null
}

# Labels the board controls. Every other label on an issue is left alone.
is_managed() { [[ "$1" =~ ^(phase:.*|plan-approved|accepted)$ ]]; }
# dev-verified is a human gate label; Board sync never sets or removes it.

wanted_labels() {
  case "$1" in
    "Backlog")     echo "phase:1-discovery" ;;
    "Design")      echo "phase:2-design" ;;
    "Technical")  echo "phase:3-technology" ;;
    "Ready")       echo "plan-approved" ;;
    "In Progress") echo "phase:4-engineering plan-approved" ;;
    "Acceptance")  echo "phase:5-acceptance" ;;
    "Release")     echo "phase:6-release" ;;
    "Done")        echo "accepted" ;;
    *)             echo "?" ;;
  esac
}

owner_for() {
  case "$1" in
    "Backlog"|"Acceptance") echo "${OWNER_PRODUCT:-}" ;;
    "Design")               echo "${OWNER_DESIGN:-}" ;;
    "Technical")           echo "${OWNER_TECH:-}" ;;
    "In Progress")          echo "${OWNER_ENG:-}" ;;
    "Release")              echo "${OWNER_RELEASE:-}" ;;
    *)                      echo "" ;;
  esac
}

checklist_for() {
  case "$1" in
    "Backlog") cat <<'EOF'
**Phase 1: Discovery** (agent: product-owner). Exit checklist:
- [ ] The problem and the people it affects are described
- [ ] The intended outcome is stated
- [ ] Requirements and acceptance criteria are written
- [ ] Concepts that came up are in docs/concepts.md, and the ones the requirements rely on are confirmed or marked pending
- [ ] Open questions are listed on the issue, with who decides each one

When it's met, move the card to **Design**.
EOF
    ;;
    "Design") cat <<'EOF'
**Phase 2: Experience Design** (agent: experience-designer). Exit checklist:
- [ ] A user flow and a low-fidelity clickable prototype exist
- [ ] Design decisions are written down
- [ ] The design lead and product owner agree the experience is right

When it's met, move the card to **Technical**.
EOF
    ;;
    "Technical") cat <<'EOF'
**Phase 3: Technical Direction** (agent: technology-architect). Exit checklist:
- [ ] The architecture summary and platform decisions are written
- [ ] Constraints and risks are listed, including steps a developer must run by hand
- [ ] The implementation plan is written, building on the Phase 1 requirements plan, and names the folders the code will go in
- [ ] The technology lead approves the plan

When the plan is approved, move the card to **Ready**.
EOF
    ;;
    "Ready") cat <<'EOF'
**Plan approved.** Ready for an engineer. Move the card to **In Progress** to start building.
EOF
    ;;
    "In Progress") cat <<'EOF'
**Phase 4: Engineering** (agent: software-engineer). Exit checklist:
- [ ] Code and tests are in a draft pull request whose description says `Refs #<issue>`
- [ ] Steps that change a shared environment are written for a developer to run
- [ ] The pull request is marked **Ready for review**: the card then moves to **Acceptance** on its own
EOF
    ;;
    "Acceptance") cat <<'EOF'
**Phase 5: Verification and Acceptance** (agent: verification-analyst). Exit checklist:
- [ ] A person has reviewed the pull request
- [ ] A human-facing test plan exists for the issue and each of its sub-issues, in `docs/acceptance/<issue-name>/test-plan.md`, and is linked on the issue
- [ ] The result is checked against the requirements, confirmed concepts, design and technology decisions
- [ ] Remaining risks and exceptions are written down and accepted
- [ ] Lessons are captured
- [ ] The pull request is merged by a person

If something fails and needs a code change, move the card back to In Progress, convert the PR to draft, fix it, then mark it Ready for review again.
When the checklist is met, move the sub-issue to **Done**. When every sub-issue is Done, move the parent to **Release**.
EOF
    ;;
    "Release") cat <<'EOF'
**Phase 6: Release** (agent: release-coordinator). Exit checklist:
- [ ] Every sub-issue is Done and its pull request merged
- [ ] The release package is in `docs/releases/<issue-name>.md` and linked here
- [ ] The release approver ran the `release` workflow and approved the `prod` environment
- [ ] Post-release checks passed (re-plan clean, contract test on `prod`, report smoke check)

When the checklist is met, move the card to **Done**. That closes the issue.
EOF
    ;;
    "Done") echo "**Accepted.** The issue is closed." ;;
  esac
}

fetch_board() {
  if [ -n "${BOARD_JSON:-}" ]; then
    cp "$BOARD_JSON" "$WORK/board.json"
    return
  fi
  # PROJECT_OWNER_TYPE: organization (default) or user (personal-account project).
  local owner_type="${PROJECT_OWNER_TYPE:-organization}"
  local q='
    query($org: String!, $num: Int!, $window: Int!) {
      __OWNER__(login: $org) {
        projectV2(number: $num) {
          items(first: 100) {
            pageInfo { hasNextPage }
            nodes {
              isArchived
              fieldValueByName(name: "Status") {
                ... on ProjectV2ItemFieldSingleSelectValue { name }
              }
              content {
                ... on Issue {
                  number
                  state
                  repository { nameWithOwner }
                  labels(first: 30) { nodes { name } }
                  assignees(first: 20) { nodes { login } }
                  comments(last: $window) { totalCount nodes { body viewerDidAuthor } }
                }
              }
            }
          }
        }
      }
    }'
  gh api graphql -F num="$PROJECT_NUMBER" -f org="$ORG" -F window="$COMMENT_WINDOW" \
    -f query="${q/__OWNER__/$owner_type}" > "$WORK/raw.json" || true
  # Normalise so the rest of the script reads .data.organization either way.
  jq '.data.organization = (.data.organization // .data.user)' "$WORK/raw.json" > "$WORK/board.json" 2>/dev/null \
    || cp "$WORK/raw.json" "$WORK/board.json"
}

sync_once() {
  fetch_board

  if ! jq -e '.data.organization.projectV2.items.nodes' "$WORK/board.json" > /dev/null 2>&1; then
    echo "::error::Could not read project #${PROJECT_NUMBER:-?} in ${ORG:-?}. Check that BOARD_TOKEN is set, not expired, and can read organization projects."
    jq -r '.errors[]?.message' "$WORK/board.json" 2>/dev/null || cat "$WORK/board.json"
    exit 1
  fi
  if jq -e '.data.organization.projectV2.items.pageInfo.hasNextPage' "$WORK/board.json" > /dev/null; then
    echo "::warning::The board has more than 100 items; only the first 100 were checked. Archive old cards."
  fi

  # last: the column named in this account's newest Board sync comment.
  # It reads the v2 marker, or the first line of a v1 comment
  # ("Issue moved to **X**"), so existing issues aren't announced again.
  # more: the issue has older comments than the ones read.
  # (Read into a variable, not a pipe, so announced_now survives the loop.)
  items=$(jq -c --arg repo "$GITHUB_REPOSITORY" '
    .data.organization.projectV2.items.nodes[]
    | select(.isArchived | not)
    | select(.content.repository.nameWithOwner? == $repo)
    | {n: .content.number, state: .content.state,
       status: (.fieldValueByName.name // ""),
       labels: [.content.labels.nodes[].name],
       assignees: [.content.assignees.nodes[]?.login],
       more: ((.content.comments.totalCount // 0) > (.content.comments.nodes | length)),
       last: ([.content.comments.nodes[]
               | select(.viewerDidAuthor)
               | ((.body | capture("<!-- board-sync:column=(?<c>[^>]*) -->") | .c)
                  // (.body | capture("^Issue moved to \\*\\*(?<c>[^*]+)\\*\\*") | .c))
              ] | last // "")}' "$WORK/board.json")

  while read -r item; do
    [ -z "$item" ] && continue
    n=$(jq -r .n <<<"$item")
    status=$(jq -r .status <<<"$item")
    state=$(jq -r .state <<<"$item")
    last=$(jq -r .last <<<"$item")
    more=$(jq -r .more <<<"$item")
    labels=$(jq -r '.labels[]' <<<"$item")
    assignees=$(jq -r '.assignees[]' <<<"$item" | tr '[:upper:]' '[:lower:]')

    [ -z "$status" ] && continue
    # Doc changes skip the phases.
    if grep -qx 'type:docs' <<<"$labels"; then continue; fi

    want=$(wanted_labels "$status")
    if [ "$want" = "?" ]; then
      if [ -z "${unknown_seen[$status]:-}" ]; then
        log "Unknown column '$status' (first seen on #$n), skipped"
        unknown_seen[$status]=1
      fi
      continue
    fi
    want=$(tr ' ' '\n' <<<"$want" | sort | xargs)
    have=$( { while read -r l; do if [ -n "$l" ] && is_managed "$l"; then echo "$l"; fi; done <<<"$labels"; } | sort | xargs)

    # Announced or repaired in this column earlier in this run: the board may
    # still show the old labels, so leave it alone rather than "repair"
    # labels that are already correct.
    [ "${announced_now[$n]:-}" = "$status" ] && continue
    [ "${repaired_now[$n]:-}" = "$status" ] && continue
    [ -n "${announced_now[$n]:-}" ] && last="${announced_now[$n]}"

    # Decide what to do.
    if [ "$last" = "$status" ]; then
      [ "$have" = "$want" ] && continue
      action=repair          # same column, labels drifted: fix quietly
    elif [ -z "$last" ] && [ "$have" = "$want" ]; then
      continue               # never announced, but already in step: leave it
    elif [ -z "$last" ] && [ "$more" = true ]; then
      # No marker in the newest comments of a busy issue: it may have been
      # announced long ago. Fix the labels quietly rather than risk a repeat.
      action=repair
    else
      action=announce        # the card is in a new column
    fi

    args=()
    for l in $have; do
      if ! tr ' ' '\n' <<<"$want" | grep -qx -- "$l"; then args+=(--remove-label "$l"); fi
    done
    for l in $want; do
      if ! tr ' ' '\n' <<<"$have" | grep -qx -- "$l"; then args+=(--add-label "$l"); fi
    done

    if [ "$action" = repair ]; then
      if write_gh issue edit "$n" --repo "$GITHUB_REPOSITORY" "${args[@]}"; then
        repaired_now[$n]="$status"
        if [ -z "$last" ]; then
          log "#$n: labels put back to match **$status** ([$have] -> [$want]); no comment (no Board sync comment in its last $COMMENT_WINDOW comments)"
        else
          log "#$n: labels put back to match **$status** ([$have] -> [$want]); no comment"
        fi
      else
        fail_issue "$n" "couldn't update labels"
      fi
      continue
    fi

    if [ "${#args[@]}" -gt 0 ] && ! write_gh issue edit "$n" --repo "$GITHUB_REPOSITORY" "${args[@]}"; then
      fail_issue "$n" "couldn't update labels"
      continue
    fi

    # Hand the issue from the previous phase owner to this column's owner.
    owner=$(login "$(owner_for "$status")")
    if [ -n "$owner" ] && [ "$state" = "OPEN" ]; then
      owners=$(phase_owners)
      a_args=()
      for a in $assignees; do
        if [ "$a" != "$owner" ] && grep -qx -- "$a" <<<"$owners"; then a_args+=(--remove-assignee "$a"); fi
      done
      grep -qx -- "$owner" <<<"$assignees" || a_args+=(--add-assignee "$owner")
      if [ "${#a_args[@]}" -gt 0 ] && ! write_gh issue edit "$n" --repo "$GITHUB_REPOSITORY" "${a_args[@]}"; then
        warn_issue "$n" "couldn't change assignees (check that the OWNER_* repo variables are GitHub usernames)"
      fi
    fi

    labels_md=$(sed -E 's/([^ ]+)/`\1`/g; s/ /, /g' <<<"$want")
    {
      echo "<!-- board-sync:column=$status -->"
      if [ -n "$last" ]; then
        echo "Card moved from **$last** to **$status**: $labels_md."
      else
        echo "Card is in **$status**: $labels_md."
      fi
      echo
      checklist_for "$status"
    } > "$WORK/comment.md"
    if ! write_gh issue comment "$n" --repo "$GITHUB_REPOSITORY" --body-file "$WORK/comment.md"; then
      fail_issue "$n" "couldn't post the checklist comment"
      continue
    fi
    announced_now[$n]="$status"
    log "#$n: ${last:-(none)} -> $status, labels [$have] -> [$want], checklist posted"
  done <<<"$items"
}

end=$(( $(date +%s) + MINUTES * 60 ))
while :; do
  sync_once
  [ "$(date +%s)" -ge "$end" ] && break
  sleep "$INTERVAL"
done

if [ "$failures" -gt 0 ]; then
  echo "::error::$failures issue update(s) failed. Every other card was synced; see the errors above."
  exit 1
fi
