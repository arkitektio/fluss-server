# Fluss-Server 


[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/arkitektio/fluss-server/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Fluss is the Arkitekt Workflow Repository. It represents a central repository of all workflows
that users have created and shared. It also provides interfaces to save and retrieve workflow
runs, and to inspect the results of these runs. Importantly fluss is **not** a workflow engine,
but rather a repository for workflows and their runs.

If you are looking for a "reactive" workflow scheduler for fluss-workflows you should look at the [Reaktion](
    https://github.com/jhnnsrs/reaktion) plugin or Rekuest, which will be able to schedule fluss workflows
    on a connected Arkitekt App (or on multiple connected apps).



## Developmental Notices

Fluss is currently being rewritten to support the modern Arkitekt Stack of [Django](https://djangoproject.com)  and [Strawberry GraphQL](https://strawberry.rocks/).
This repository will remain the main repository for Fluss, and the new version will be merged into this repository once the new version is ready for production.


