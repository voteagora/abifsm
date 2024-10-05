========================
ABI Fragment Set Manager
========================


.. image:: https://img.shields.io/pypi/v/abifsm.svg
        :target: https://pypi.python.org/pypi/abifsm

.. image:: https://img.shields.io/travis/voteagora/abifsm.svg
        :target: https://travis-ci.com/voteagora/abifsm

.. image:: https://readthedocs.org/projects/abifsm/badge/?version=latest
        :target: https://abifsm.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


A library for working with sets of EVM contracts and their ABIs, mostly for getting consistent naming conventions and working with topics.

Basically syntatic sugar for...
* Iterating over (sorted) events
* Looking up ABI by topic
* Getting the topic from an ABI
* Creating postgres-compatible names that are internally unique against a set of contracts

Plus...

* You can diff ABIs

Also...

* Free software: MIT license
* Documentation: https://abifsm.readthedocs.io.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
