# Silexdata MySQL Release Notes

**Topics**

- <a href="#v1-0-2">v1\.0\.2</a>
    - <a href="#bugfixes">Bugfixes</a>
- <a href="#v1-0-1">v1\.0\.1</a>
    - <a href="#minor-changes">Minor Changes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
    - <a href="#release-summary">Release Summary</a>
    - <a href="#minor-changes-1">Minor Changes</a>

<a id="v1-0-2"></a>
## v1\.0\.2

<a id="bugfixes"></a>
### Bugfixes

* galaxy\.yml \- declare GPL\-3\.0\-or\-later\, the license of the inventory plugin\, alongside Apache\-2\.0\. The collection declared only Apache\-2\.0 before\.
* inventory \- document <code>silexdata\.mysql\.inventory</code> as the only accepted <code>plugin</code> value\. The short name <code>inventory</code> was documented but always refused by Ansible\.
* inventory \- report that the <code>pymysql</code> Python library is required when it is not installed\, instead of failing to load the plugin\.
* inventory \- store the refreshed inventory in the cache on <code>\-\-flush\-cache</code>\. It was re\-read from the database but not cached\, so the next cached run still served the old data\.

<a id="v1-0-1"></a>
## v1\.0\.1

<a id="minor-changes"></a>
### Minor Changes

* inventory \- Added environment variable option for <code>db\_host</code>\, <code>db\_port</code>\, <code>db\_user</code>\, <code>db\_password</code>\, and <code>db\_name</code> options\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary"></a>
### Release Summary

Initial release of the silexdata\.mysql Ansible Collection\.

<a id="minor-changes-1"></a>
### Minor Changes

* Added an inventory plugin for MySQL\.
* Set up the collection structure\, licensing\, and documentation\.
