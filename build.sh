set -o errexit
set -o nounset
set -o pipefail
#set -x

# Check that the usage is correct
if [ ! $# -eq 0 ]
then
  echo "Usage: bash build.sh"
  exit
fi

echo "Finding the version..."
GIT_COMMIT="$(git rev-parse HEAD)"
ISODATE="$(date +%Y-%m-%dT%H:%M:%S%z)"
DEPLOY_TAG="${ISODATE:0:10}--${GIT_COMMIT:0:8}"
IMAGE_NAME="emeraldsci/cloudcompchem:$DEPLOY_TAG"

echo "Building..."
docker build -t "$IMAGE_NAME" .
# docker push $IMAGE_NAME

echo "Building $IMAGE_NAME complete!"

echo
echo "========================================================================="
echo "== To deploy this, please email tachyon@emeraldcloudlab.com with your  =="
echo "== image name                                                          =="
echo "========================================================================="
echo
echo "Image Name: $IMAGE_NAME"
echo
