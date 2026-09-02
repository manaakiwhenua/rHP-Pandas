#!/usr/bin/env bash
#
# Release rhppandas: run the tests, build and check dist/ locally, push an
# annotated tag and open a draft GitHub release for hand editing.
#
# Publishing the release on GitHub triggers .github/workflows/publish.yml,
# which rebuilds the package and uploads it to PyPI with trusted publishing.
# No PyPI tokens are needed on this machine.
#
# Usage: scripts/release.sh [--bump RULE] [--test-pypi] [--dry-run] [--skip-tests]
#
#   --bump RULE   first bump the version in pyproject.toml with `poetry version
#                 RULE` (patch, minor, major, or an explicit version such as
#                 0.4.0rc1), commit it as "Bump version to X.Y.Z" and push it
#                 to develop. Without this, bump and push the version by hand.
#   --test-pypi   do not tag or release; instead run the publish workflow
#                 against TestPyPI from the current develop, to rehearse.
#   --dry-run     run the local steps (tests, build, twine check) and print
#                 the tag, release or workflow commands instead of running them.
#   --skip-tests  do not run pytest first.
#
# Run from a clean checkout of develop that matches origin/develop, with
# the version in pyproject.toml already bumped or --bump given. Needs git,
# gh (authenticated),
# poetry, twine and python >= 3.11 on PATH.

set -euo pipefail

BUMP=""
TEST_PYPI=0
DRY_RUN=0
SKIP_TESTS=0

usage() { sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; }
log()   { printf '\n==> %s\n' "$*"; }
die()   { printf 'release: %s\n' "$*" >&2; exit 1; }
run()   { if (( DRY_RUN )); then printf '(dry-run) %s\n' "$*"; else "$@"; fi; }

while (( $# )); do
    case "$1" in
        --bump)       [[ $# -ge 2 ]] || die "--bump needs a rule: patch, minor, major or a version"
                      BUMP="$2"; shift ;;
        --test-pypi)  TEST_PYPI=1 ;;
        --dry-run)    DRY_RUN=1 ;;
        --skip-tests) SKIP_TESTS=1 ;;
        -h|--help)    usage; exit 0 ;;
        *)            die "unknown option: $1 (try --help)" ;;
    esac
    shift
done

cd "$(git rev-parse --show-toplevel)"

# ---- tooling -----------------------------------------------------------------
for tool in git gh poetry twine python; do
    command -v "$tool" >/dev/null || die "$tool not found on PATH"
done
# A stale launcher (e.g. ~/.local/bin/twine pointing at a Python without twine)
# fails here rather than after the build.
twine --version >/dev/null 2>&1 || die "twine at $(command -v twine) does not run; activate the environment that has it"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated (run: gh auth login)"

# ---- version and repository state -------------------------------------------
BRANCH=$(git rev-parse --abbrev-ref HEAD)

[[ "$BRANCH" == "develop" ]] || die "release from develop, not $BRANCH"
[[ -z "$(git status --porcelain)" ]] || die "working tree is not clean"
git fetch -q origin develop --tags
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/develop)" ]] \
    || die "develop differs from origin/develop; push or pull first"

export POETRY_VIRTUALENVS_CREATE=false  # never create a .venv in the checkout
VERSION=$(poetry version --short)
if [[ -n "$BUMP" ]]; then
    (( TEST_PYPI )) && die "--bump cannot be combined with --test-pypi; a rehearsal does not change the version"
    # Work out the new version first so the guards below check the right tag.
    if ! bump_output=$(poetry version --dry-run "$BUMP" 2>&1); then
        die "poetry version could not apply rule '$BUMP': $bump_output"
    fi
    VERSION=$(sed -n 's/.* to //p' <<<"$bump_output")
    [[ -n "$VERSION" ]] || die "could not read the new version from: $bump_output"
fi
TAG="v$VERSION"

if (( ! TEST_PYPI )); then
    if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
        die "tag $TAG already exists; bump version in pyproject.toml"
    fi
    if gh release view "$TAG" >/dev/null 2>&1; then
        die "GitHub release $TAG already exists"
    fi
    if command -v curl >/dev/null \
       && curl -sf -o /dev/null "https://pypi.org/pypi/rhppandas/$VERSION/json"; then
        die "rhppandas $VERSION is already on PyPI"
    fi
fi

log "Releasing rhppandas $VERSION from $(git rev-parse --short HEAD)"
(( TEST_PYPI )) && echo "TestPyPI rehearsal: no tag or GitHub release will be created"
(( DRY_RUN ))   && echo "Dry run: bump, tag, release and workflow commands are printed, not executed"

# ---- optional version bump ---------------------------------------------------
# Committed straight to develop, as previous "Bump version" commits were. If a
# later step fails, the bump stays in place: fix the problem and rerun without
# --bump.
if [[ -n "$BUMP" ]]; then
    log "Bumping version to $VERSION"
    run poetry version "$BUMP"
    run git commit -q -m "Bump version to $VERSION" pyproject.toml
    run git push origin develop
    (( DRY_RUN )) && echo "(dry-run) note: dist/ below is built from the current version, not $VERSION"
fi

# ---- tests -------------------------------------------------------------------
if (( SKIP_TESTS )); then
    log "Skipping tests (--skip-tests)"
else
    log "Running tests"
    python -m pytest -q
fi

# ---- build and check ---------------------------------------------------------
# The workflow rebuilds from the tag before uploading; this local build only
# catches packaging problems before anything is tagged.
log "Building dist/"
rm -rf dist
poetry build

log "Checking dist/"
twine check dist/*
ls -l dist/

# ---- TestPyPI rehearsal ------------------------------------------------------
if (( TEST_PYPI )); then
    log "Running the publish workflow against TestPyPI"
    run gh workflow run publish.yml --ref develop -f target=testpypi
    cat <<MSG

Done. Follow the run with: gh run watch
To try the TestPyPI package, use index https://test.pypi.org/simple/ with
https://pypi.org/simple as an extra index (dependencies are not on TestPyPI)
and request rhppandas==$VERSION.
MSG
    exit 0
fi

# ---- tag and draft release ---------------------------------------------------
log "Tagging $TAG"
run git tag -a "$TAG" -m "rhppandas $VERSION"
run git push origin "$TAG"

log "Creating draft GitHub release $TAG"
run gh release create "$TAG" --draft --verify-tag --title "$TAG" --generate-notes

cat <<MSG

Done. Next steps:
  1. Edit the draft release notes on GitHub (call out dependency floors and
     behaviour changes, which the generated PR list will not), then publish.
     Publishing runs the tests, rebuilds the package, uploads it to PyPI and
     attaches the sdist and wheel to the release. Follow it with: gh run watch
  2. The conda-forge autotick bot opens a PR on
     https://github.com/conda-forge/rhppandas-feedstock a few hours after the
     PyPI upload. It only bumps version and hash: check the recipe's run
     requirements against pyproject.toml before merging.
MSG
