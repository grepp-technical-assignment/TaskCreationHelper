# TCH Runner

This project is a simple runner for TCH in command line interface.

# Dependencies

## Operating System

* Linux
* MacOS X

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

* Optimize version control
* Check if the docker image is installed

# Changelog

## v0.1

* First version of TCH Runner.