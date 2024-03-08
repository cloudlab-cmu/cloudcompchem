set -o errexit
set -o nounset
set -o pipefail
#set -x

# Check that the usage is correct
if [ ! $# -eq 0 ]
then
  echo "Usage: bash deploy/build.sh"
  exit
fi

echo "Finding the version..."
GIT_COMMIT="$(git rev-parse HEAD)"
ISODATE="$(date +%Y-%m-%dT%H:%M:%S%z)"
DEPLOY_TAG="${ISODATE:0:10}--${GIT_COMMIT:0:8}"
IMAGE_NAME="emeraldsci/tachyon:$DEPLOY_TAG"

echo "Building..."
docker build --pull -f deploy/Dockerfile -t "$IMAGE_NAME" ..
docker push $IMAGE_NAME

echo "Building $IMAGE_NAME complete!"

echo
echo "========================================================================="
echo "== To deploy this, please email tachyon@emeraldcloudlab.com with your  =="
echo "== image name and the constellation id of the simulation this image    =="
echo "== supports.                                                           =="
echo "========================================================================="
echo
echo "Image Name: $IMAGE_NAME"
echo 
