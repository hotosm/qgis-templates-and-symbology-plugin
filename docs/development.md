---
hide:
  - navigation
---
  
## Install instructions


## Install the plugin into QGIS


## Testing

The plugin contains a bash script `run-tests.sh` in the root folder that can be used to run the 
all the plugin tests locally for QGIS 3.16 and 3.20 versions on a linux based OS.
The script uses the QGIS official docker images, in order to use it, docker images for QGIS version 3.16 and 3.20
need to be present.

Run the following commands in linux shell to pull the images and execute the script for tests.

```
docker pull qgis/qgis:release-3_16
docker pull qgis/qgis:release-3_22
```

```
./run-tests.sh
```

GitHub actions workflow is provided by the plugin to run tests in QGIS 3.16, 3.18, 3.20 and 3.22 versions in 
the plugin repository, the workflow is located in the following directory `.github/workflow/ci.yml`


## Building documentation