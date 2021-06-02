=======================
PyDyTuesday Downloader
=======================

A Python library to automatically download TidyTuesday datasets, inspired by the tidytuesdayR package for r.

The package is best installed directly from github 
.. code:: python

    pip install git+https://github.com/AndreasThinks/PyDyTuesday#egg=PyDyTuesday

It can also be downloaded from PyPi 

.. code:: python

    pip install PyDyTuesday


Contains two functions:

.. code:: python

    #obtain dataset from specific date
    get_date("2021-01-19")

    #specific week
    get_week(2019, 3)