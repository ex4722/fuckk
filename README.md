# Fuckk
Author: **thy.isnis**

_Fix's `printk` for linux kernel binaries by replacing it with corresponding printk macro_

## Description:

`printk` in the linux kernel take's a string but also a logging level with is appended to the string. This can cause string's to start with non ascii bytes which in turn cause binja to not render them properly. This plugin replace those call's with the corresponding macro such as `pr_error` or `pr_alert`.

## License

This plugin is released under an [MIT license](./license).
