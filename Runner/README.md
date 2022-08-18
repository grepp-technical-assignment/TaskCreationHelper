# TCH Runner

This project is a simple runner for TCH in command line interface.

# Dependencies

## Operating System

* Linux
* MacOS X
* Windows

## Programming Language

* C99
* make

## TaskCreationHelper

* TaskCreationHelper's docker image

# Usage

## Installation

Enter this command to install tch runner.

~~~shell
 $ make install
~~~

In Windows OS, you need to setting PATH environment variable. append `.../TaskCreationHelper/Runner/bin` to PATH.

## Uninstallation

Enter this command to uninstall tch runner.

~~~shell
 $ make uninstall
~~~

## Run

Enter this command on termianl to learn usage.

~~~shell
 $ tch --help
~~~

You can use TCH Runner like this.

~~~shell
 $ tch /Users/..../Example/SortTheList/config.json
 TaskCreationHelper$ tch Example/SortTheList -l generate
 TaskCreationHelper$ tch Example/SortTheList/config.json -l full
 TaskCreationHelper/Runner$ tch ../Example/SortTheList/config.json
 TaskCreationHelper/Example/SortTheList$ tch ./ 
 TaskCreationHelper/Example/SortTheList$ tch config.json
~~~

# TODO

* Check if the docker image is installed
* Remove system function to docker run & use docker api

# Changelog

## v0.1

* First version of TCH Runner.

## v0.2

* Add invocation level option.
* Now TCH Runner supports native Windows.

## v0.3

* TCH Runner supports `-i`, `--init` option.
* TCH Runner supports `-t`, `--text_filter` option.