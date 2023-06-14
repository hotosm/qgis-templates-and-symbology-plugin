# HOT QGIS Templates and Symbology plugin


![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/hotosm/qgis-templates-and-symbology-plugin/ci.yml?branch=master)
![GitHub](https://img.shields.io/github/license/hotosm/qgis-templates-and-symbology-plugin)

QGIS plugin for managing map templates and symbology from HOTOSM and associated Open Mapping Hubs. 

### Installation

#### Install from QGIS plugin repository

- Open QGIS application and open plugin manager.
- Search for `HOT Templates and Symbology Manager` in the All page of the plugin manager.
- From the found results, click on the `HOT Templates and Symbology Manager` result item and a page with plugin information will show up. 
  
- Click the `Install Plugin` button at the bottom of the dialog to install the plugin.


#### Install from ZIP file

Alternatively the plugin can be installed using **Install from ZIP** option on the 
QGIS plugin manager. 

- Download zip file from the required plugin released version
https://github.com/hotosm/qgis-templates-and-symbology-plugin/releases/download/{tagname}/qgis_templates_symbology.{version}.zip

- From the **Install from ZIP** page, select the zip file and click the **Install** button to install plugin

### Usage

Please see the [HOT QGIS Templates and Symbology Plugin User Guide](https://docs.google.com/document/d/1wjY1n55xN0jRo7TukyjTjELMTabzD2ux6izqhRhjjMo/edit#).


### Development 

To use the plugin for development purposes, clone the repository locally,
install pip, a python dependencies management tool see https://pypi.org/project/pip/

#### Create virtual environment

Using any python virtual environment manager create project environment. 
Recommending to use [virtualenv-wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/).

It can be installed using python pip 

```
pip install virtualenvwrapper
```

 1. Create virtual environment

    ```
    mkvirtualenv templates_symbology
    ```

2. Using the pip, install plugin development dependencies by running 

    ```
    pip install -r requirements-dev.txt
   ```


To install the plugin into the QGIS application, activate virtual environment and then use the below command

```
 python admin.py install
```
 ### Get Involved
 If you are interested in testing the plugin, sharing your feedback and contributing to this repository, please follow our [Contributing Guidelines](https://github.com/hotosm/qgis-templates-and-symbology-plugin/blob/master/CONTRIBUTING.md)
