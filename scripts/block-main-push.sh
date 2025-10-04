CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "!!! Push to 'main' branch is forbidden. Please use a pull request. !!!"
  exit 1
else
  exit 0
fi
