# QGIS Templates and Symbology plugin

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/hotosm/qgis-templates-symbology-plugin/Continuous%20Integration)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/hotosm/qgis-templates-symbology-plugin/?include_prereleases)
![GitHub](https://img.shields.io/github/license/hotosm/qgis-templates-symbology-plugin)

QGIS plugin for managing map templates and symbology

Site https://hotosm.github.io/qgis-templates-symbology-plugin/

### Installation

During the development phase the plugin is available to install via 
a dedicated plugin repository 
https://hotosm.github.io/qgis-templates-symbology-plugin/repository/plugins.xml

Open the QGIS plugin manager, then select the **Settings** page, click **Add** 
button on the **Plugin Repositories** group box and use the above url to create
the new plugin repository.
![Add plugin repository](docs/images/plugin_settings.png)

After adding the new repository, the plugin should be available from the list
of all plugins that can be installed.

**NOTE:** While the development phase is on going the plugin will be flagged as experimental, make
sure to enable the QGIS plugin manager in the **Settings** page to show the experimental plugins
in order to be able to install it.

Alternatively the plugin can be installed using **Install from ZIP** option on the 
QGIS plugin manager. Download zip file from the required plugin released version
https://github.com/hotosm/qgis-templates-symbology-plugin/releases/download/{tagname}/qgis_templates_symbology.{version}.zip.

From the **Install from ZIP** page, select the zip file and click the **Install** button to install
plugin
![Screenshot for install from zip option](docs/images/install_from_zip.png)

When the development work is complete the plugin will be available on the QGIS
official plugin repository.


#### Development 

To use the plugin for development purposes, clone the repository locally,
install pip, a python dependencies management tool see https://pypi.org/project/pip/

##### Create virtual environment

Using any python virtual environment manager create project environment. 
Recommending to use [virtualenv-wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/).

It can be installed using python pip 

```
pip install virtualenvwrapper
```

 1. Create virtual environment

    ```
    mkvirtualenv qgis_templates_symbology
    ```

2. Using the pip, install plugin development dependencies by running 

    ```
    pip install -r requirements-dev.txt
   ```


To install the plugin into the QGIS application, activate virtual environment and then use the below command

```
 python admin.py install
```


